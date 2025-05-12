import random
import socket
import uiautomator2 as u2
import types
import rtree
import re
from typing import Dict, List, Union
from xml.etree import ElementTree
from .absDriver import AbstractScriptDriver, AbstractStaticChecker, AbstractDriver
from .adbUtils import list_forwards, remove_forward, create_forward


"""
The definition of U2ScriptDriver
"""
class U2ScriptDriver(AbstractScriptDriver):
    """
    This is the ScriptDriver used to send ui automation request in Property
    When you interact with the mobile in properties. You will use the object here
    
    *e.g. the following self.d use U2ScriptDriver*
    ```
    @precondition(...)
    def test_battery(self):
        self.d(text="battery").click()
    ```
    """

    deviceSerial: str = None
    
    @classmethod
    def setDeviceSerial(cls, deviceSerial):
        cls.deviceSerial = deviceSerial
    
    def __init__(self):
        self.d = None

    def getInstance(self):
        if self.d is None:
            self.d = (
                u2.connect() if self.deviceSerial is None
                else u2.connect(self.deviceSerial)
            )
            
            def get_u2_forward_port() -> int:
                """rewrite forward_port mothod to avoid the relocation of port
                :return: the new forward port
                """
                print("Rewriting forward_port method")
                self.d._dev.forward_port = types.MethodType(
                                forward_port, self.d._dev)
                lport = self.d._dev.forward_port(8090)
                setattr(self.d._dev, "msg", "meta")
                print(f"[U2] local port: {lport}")
                return lport
            
            self._remove_remote_port(8090)
            self.d.lport = get_u2_forward_port()
            self._remove_remote_port(9008)

        return self.d
    
    def tearDown(self):
        self.d.stop_uiautomator()
    
    def _remove_remote_port(self, port:int):
        """remove the forward port
        """
        forwardLists = list_forwards(device=self.deviceSerial)
        for forward in forwardLists:
            if forward["remote"] == f"tcp:{port}":
                forward_local = forward["local"]
                remove_forward(local_spec=forward_local, device=self.deviceSerial)
        

"""
The definition of U2StaticChecker
"""
class StaticU2UiObject(u2.UiObject):
    def __init__(self, session, selector):
        self.session: U2StaticDevice = session
        self.selector = selector

    @property
    def exists(self):
        def filterU2Keys(originKey):
            filterDict = {
                "resourceId": "resource-id"
            }
            if filterDict.get(originKey, None):
                return filterDict[originKey]
            return originKey
        
        def getXPath(kwargs: Dict[str, str]):
            attrLocs = list()
            SPECIAL_KEY = {"mask", "childOrSibling", "childOrSiblingSelector"}
            for key, val in kwargs.items():
                if key in SPECIAL_KEY:
                    continue
                key = filterU2Keys(key)
                attrLocs.append(f"[@{key}='{val}']")
            # filter the covered widgets
            attrLocs.append("[@covered='false']")
            xpath = f".//node{''.join(attrLocs)}"
            return xpath

        def getXMLCoveredINFO(xml):
            """
            Algorithm: Filter the hidden widgets.
            Set `covered` xml info according to drawing orders.
            """
            pass
        
        xpath = getXPath(self.selector)
        return self.session.xml.find(xpath) is not None


def _get_bounds(raw_bounds):
    pattern = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
    m = re.match(pattern, raw_bounds)
    try:
        bounds = [int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))]
    except Exception as e:
        print(f"raw_bounds: {raw_bounds}")
        print(f"Please report this bug to Kea2")
        raise RuntimeError(e)
        
    return bounds


class _HindenWidgetFilter:
    def __init__(self, hierarchy):
        # self.global_drawing_order = 0
        self._nodes = []

        self.idx = rtree.index.Index()
        self.set_covered_attr(hierarchy)
        # hierarchy.write("filterd_tree.xml", xml_declaration=True, encoding="utf-8")
        # pass

    def _iter_by_drawing_order(self, ele: ElementTree.Element):
        """
        iter by drawing order (DFS)
        """
        if ele.tag == "node":
            yield ele

        children = list(ele)
        try:
            children.sort(key=lambda e: int(e.get("drawing-order", 0)))
        except (TypeError, ValueError):
            pass

        for child in children:
            yield from self._iter_by_drawing_order(child)
   
    def set_covered_attr(self, tree: ElementTree):
        root: ElementTree.Element = tree.getroot()
        self._nodes: List[ElementTree.Element] = list()
        for e in self._iter_by_drawing_order(root):
            # e.set("global-order", str(self.global_drawing_order))
            # self.global_drawing_order += 1
            e.set("covered", "false")

            # algorithm: filter by "clickable"
            clickable = (e.get("clickable", "false") == "true")
            _raw_bounds = e.get("bounds")
            if _raw_bounds is None:
                continue
            bounds = _get_bounds(_raw_bounds)
            if clickable:
                covered_widget_ids = list(self.idx.contains(bounds))
                if covered_widget_ids:
                    for covered_widget_id in covered_widget_ids:
                        node = self._nodes[covered_widget_id]
                        node.set("covered", "true")
                        self.idx.delete(
                            covered_widget_id,
                            _get_bounds(self._nodes[covered_widget_id].get("bounds"))
                        )

            cur_id = len(self._nodes)
            center = [
                (bounds[0] + bounds[2]) / 2,
                (bounds[1] + bounds[3]) / 2
            ]
            self.idx.insert(
                cur_id,
                (center[0], center[1], center[0], center[1])
            )
            self._nodes.append(e)

class U2StaticDevice(u2.Device):
    def __init__(self):
        self.xml_raw = None
        self.xml = None

    def __call__(self, **kwargs):
        return StaticU2UiObject(session=self, selector=u2.Selector(**kwargs))

    @property
    def xpath(self) -> u2.xpath.XPathEntry:
        def get_page_source(self):
            # print("[Debug] Using static get_page_source method")
            return u2.xpath.PageSource.parse(self._d.xml_raw)
        xpathEntry = u2.xpath.XPathEntry(self)
        xpathEntry.get_page_source = types.MethodType(
            get_page_source, xpathEntry
        )
        return xpathEntry


class U2StaticChecker(AbstractStaticChecker):
    """
    This is the StaticChecker used to check the precondition.
    We use the static checker due to the performing issues when runing multi-properties.
    
    *e.g. the following self.d use U2StaticChecker*
    ```
    @precondition(lambda self: self.d("battery").exists)
    def test_battery(self):
        ...
    ```
    """
    def __init__(self):
        self.d = U2StaticDevice() 

    def setHierarchy(self, hierarchy: str):
        self.d.xml_raw = hierarchy
        with open("tmp.xml", "w", encoding='utf-8') as fp:
            fp.write(hierarchy)
            fp.flush()
        self.d.xml = ElementTree.parse("tmp.xml")
        # filter the hidden widget
        _HindenWidgetFilter(self.d.xml)

    def getInstance(self, hierarchy: str):
        self.setHierarchy(hierarchy)
        return self.d


"""
The definition of U2Driver
"""
class U2Driver(AbstractDriver):
    scriptDriver = None
    staticChecker = None
    
    @classmethod
    def setDeviceSerial(cls, deviceSerial):
        U2ScriptDriver.setDeviceSerial(deviceSerial)

    @classmethod
    def getScriptDriver(self):
        if self.scriptDriver is None:
            self.scriptDriver = U2ScriptDriver()
        return self.scriptDriver.getInstance()

    @classmethod
    def getStaticChecker(self, hierarchy):
        if self.staticChecker is None:
            self.staticChecker = U2StaticChecker()
        return self.staticChecker.getInstance(hierarchy)


"""
Other Utils
"""
def forward_port(self, remote: Union[int, str]) -> int:
        """forward remote port to local random port"""
        remote = 8090
        if isinstance(remote, int):
            remote = "tcp:" + str(remote)
        for f in self.forward_list():
            if (
                f.serial == self._serial
                and f.remote == remote
                and f.local.startswith("tcp:")
            ):  # yapf: disable
                return int(f.local[len("tcp:") :])
        local_port = get_free_port()
        self.forward("tcp:" + str(local_port), remote)
        return local_port


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def get_free_port():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        try:
            return s.getsockname()[1]
        finally:
            s.close()
    except OSError:
        # bind 0 will fail on Manjaro, fallback to random port
        # https://github.com/openatx/adbutils/issues/85
        for _ in range(20):
            port = random.randint(10000, 20000)
            if not is_port_in_use(port):
                return port
        raise RuntimeError("No free port found")
