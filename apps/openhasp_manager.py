import openhasp as oh
import openhasp.mdi as mdi
from openhasp import Manager, ComposedObj, triggerFactory_entityChange
from openhasp.style1 import style as myStyle
from homeassistant.helpers.template import Template

import math
def alarm2state(design, state):
    if state == "disarmed":
        text = "DISARMED"
    elif state == "armed_home":
        text = "ARMED HOME"
    elif state == "armed_away":
        text = "ARMED AWAY"
    elif state in ["pending", "triggered"]:
        text = "ALARM TRIGGERED!"
    else:
        text = "<unknown>"
    return text

def alarm2icon(design, state):
    if state == "disarmed":
        text = "\uE565"
    elif state == "armed_home":
        text = "\uE68A"
    elif state == "armed_away":
        text = "\uE99D"
    elif state in ["pending", "triggered"]:
        text = "\uE73C2E"
    else:
        text = "\uE73C2E"
    return text

def alarm2color(design, state):
    if state == "disarmed":
        color = "green"
    elif state == "armed_home":
        color = "orange"
    elif state == "armed_away":
        color = "orange"
    elif state in ["pending", "triggered"]:
        color = "red"
    else:
        color = "red"
    return color

    def _onAlarmChange(self):
        log.info("UPDATE ALARM STATE")
        if alarm_control_panel.alarmo == "disarmed":
            self.alarm_icon.setText("\uE565")
            self.alarm_icon.setTextColor("green")
        elif alarm_control_panel.alarmo == "armed_home":
            self.alarm_icon.setText("\uE68A")
            self.alarm_icon.setTextColor("blue")
        elif alarm_control_panel.alarmo == "armed_away":
            self.alarm_icon.setText("\uE99D")
            self.alarm_icon.setTextColor("blue")
        elif alarm_control_panel.alarmo in ["pending", "triggered"]:
            self.alarm_icon.setText("\uE73C2E")
            self.alarm_icon.setTextColor("red")
        else:
            self.alarm_icon.setText("\uE73C2E")
            self.alarm_icon.setTextColor("#EDF021")


def transformOnOff(design, value):
    if value == "on":
        return f"The light is ON #FFFF00 {oh.ICON_LIGHTBULB_ON}#"
    else:
        return f"The light is OFF {oh.ICON_LIGHTBULB}"

def transformTime(design, value):
    t = value.split(":")
    return f"{t[0]}h {t[1]}m"


class MyComposedObj(ComposedObj):
    def __init__(self, design, coord, size, nbSegments, angleStep, color):
        self.ComposedObj__init__(design)
        self.nbSegments = nbSegments
        self.coord = coord
        self.size = size
        self.angle = 0
        self.angleStep = angleStep
        self.visible = False
        self.cx = coord[0] + size[0]//2
        self.cy = coord[1] + size[1]//2
        self.r = min(size)//2
        design.registerForTimerTick(self)
        self.lineObj = oh.Line(design, (coord, coord), width=2, color=color)
        self.labelObj = oh.Label(design, (self.cx-50, self.cy-25), (100,50), "Angle", textColor=color)

    def updateLineObject(self):
        points = []
        for i in range(self.nbSegments+1):
            a = (self.angle + 360/self.nbSegments*i) / 180 * math.pi
            points.append((self.cx + math.cos(a) * self.r, self.cy + math.sin(a) * self.r))
        self.lineObj.setPoints(points)
        self.labelObj.setText(f"{self.angle:d}\u00B0")

        self.angle += self.angleStep
        if self.angle > 360:
            self.angle -= 360
        if self.angle < 0:
            self.angle += 360

    def onTimerTick(self):
        if self.visible:
            self.updateLineObject()

class HaspManager(Manager):

    def __init__(self, friendlyName, name, screenSize):
        self.Manager__init__(name, screenSize, keepHAState=True, style=myStyle)   # Workaround as calling super() is not supported by pyscript
        self.logTimeEvents = False
        self.logEntityEvents = True
        self.friendlyName = friendlyName
        #self.trigger_alarm_change = triggerFactory_entityChange('alarm_control_panel.alarmo', self.alarm_state_change, 'alarm_state_change', callNow=False)

        #self.sendPeriodicHeatbeats()
        design = self.design
        dy = 30
        y = 0
        # Header
        oh.Button(design, coord=(0, y), size=(240, 30), text="Mudroom", font=1, align="left", extraPar={"radius": 0, "click":0, "bg_grad_dir":0, "bg_color":"#0027FF"})

        # Time
        obj = oh.Label(design, coord=(3, y+5), size=(62, 30), text="", font=1, align="left", extraPar={"click":0})
        obj.linkText("sensor.time_template")

        # Temperature
        obj = oh.Label(design, coord=(175, y+5), size=(45, 30), text="", font=1, align="Right", extraPar={"click":0})
        obj.linkText("sensor.home_realfeel_temperature")
        oh.Label(design, coord=(220, y+5), size=(45, 30), text="\u00b0F", font=1, align="Left", extraPar={"click":0})

        oh.Page(design, 1, isStartupPage=True)
        y += dy

        # Alarm
        oh.Label(design, coord=(69, y+12), size=(100, 30), text="Alarm System", font=16, align="left", textColor="black", extraPar={"click":0})
        self.alarm_text = oh.Label(design, coord=(69, y+32), size=(100, 30), text="", font=14, align="left", textColor="black", extraPar={"click":0})
        self.alarm_text.linkText("alarm_control_panel.alarmo", transform=alarm2state)
        self.alarm_text.linkColor("alarm_control_panel.alarmo", transform=alarm2color)
        self.alarm_icon = oh.Label(design, coord=(10, y+5), size=(50, 60), text="", font=44, align="Left", textColor="black", extraPar={"click":0})
        self.alarm_icon.linkText("alarm_control_panel.alarmo", transform=alarm2icon)
        self.alarm_icon.linkColor("alarm_control_panel.alarmo", transform=alarm2color)
        self.alarm_btn = oh.Button(design, coord=(0, y-10), size=(240, y+75), text="", extraPar={"opacity":0})
        self.alarm_btn.actionOnPush(self._onAlarmBtnPushed)
        y += 30

        oh.Page(design, 2)
        #self.gotoPage(2)
        self.alarm_pin_display = oh.Label(design, coord=(0, 40), size=(240, 30), text="", font=16, align="Center", textColor="black", extraPar={"click":0})
        self.alarm_pin = ""
        y=70
        self.arm_mode = "alarm_arm_home"
        self.alarm_keypad = oh.BtnMatrix(design, coord=(10, y), size=(220,210), options=["1","2","3","\n","4","5","6","\n","7","8","9","\n","*","0","##"],
            actionOnValFunc=self._alarmKeypadActionOnVal, extraPar={"border_side":15, "text_font40":20})
        self.alarm_arm_modes = oh.BtnMatrix(design, coord=(10, y+210), size=(220,40), options=["\uE68A Arm Home","\uE99D Arm Away"], extraPar={"toggle":1,"one_check":1,"val":0, "bg_opa":0, "border_opa":0}, actionOnValFunc=self._alarmModeActionOnVal)
        self.alarm_disarm = oh.Label(design, coord=(10, y+215), size=(220,25), text="Disarm", textColor="red")
        
    def _onAlarmBtnPushed(self, cookie):
        self.alarm_arm_modes.visible(alarm_control_panel.alarmo == 'disarmed')
        self.alarm_disarm.visible(alarm_control_panel.alarmo != 'disarmed')
        self.alarm_pin = ""
        self.alarm_pin_display.setParam('text',"")
        self.gotoPage(2)

    def _alarmModeActionOnVal(self, obj, val):
        if val == 0:
            self.arm_mode = "alarm_arm_home"
        else:
            self.arm_mode = "alarm_arm_away"

    def _alarmKeypadActionOnVal(self, obj, val):
        self.alarm_pin += str(val + 1)
        self.alarm_pin_display.setParam('text', '*' * len(self.alarm_pin))
        if len(self.alarm_pin) >= 4:
            self.alarm_pin_display.setParam('text', '')
            if self._validate_pin(self.alarm_pin):
                if alarm_control_panel.alarmo == "disarmed":
                    if self.arm_mode == "alarm_arm_away":
                        alarmo.arm(entity_id="alarm_control_panel.alarmo", mode="away")
                        action_msg = "ARMING: AWAY"
                    else:
                        alarmo.arm(entity_id="alarm_control_panel.alarmo", mode="home")
                        action_msg = "ARMING: HOME"
                    self.design.msgbox.message(text=action_msg, options=[], auto_close=2000, extraPar={"x":0,"y":100,"w":240,"h":40,"value_font":22,"bg_color":"#A8290E","text_color":"#FFFFFF","border_color": "#5B0000","radius":10,"border_side":15,"click":0,"bg_grad_dir":"0", "click":0})
                else:
                    action_msg = "DISARMING"
                    alarmo.disarm(entity_id="alarm_control_panel.alarmo")
                    self.design.msgbox.message(text=action_msg, options=[], auto_close=2000, extraPar={"x":0,"y":100,"w":240,"h":40,"value_font":22,"bg_color":"#03AA00","text_color":"#000000","border_color": "#015B00","radius":10,"border_side":15,"click":0,"bg_grad_dir":"0", "click":0})
                self.gotoPage(1)
            else:
                log.info('INVALID')
                self.design.msgbox.message(text="INVALID PIN", options=[], auto_close=1000, extraPar={"x":0,"y":100,"w":240,"h":40,"value_font":22,"bg_color":"#A8290E","text_color":"#FFFFFF","border_color":"#5B0000","radius":10,"border_side":15,"click":0,"bg_grad_dir":"0", "click":0})
            self.alarm_pin = ""

    def _validate_pin(self, input_pin):
        pin_codes_template = Template( "{{ expand(label_entities('pin_codes')) | map(attribute='state') | join(' ') }}", hass)
        return input_pin in pin_codes_template.async_render()

    def alarm_state_change(self, cookie):
        if self.design.currPageNbr == 2:
            self.gotoPage(1)

    # TODO:
    #   - if on page 2 and timeout, go to page 1


managers = [] # This needs to be global so that it remains in scope

@time_trigger("startup")
def main():
    # Create a Hasp manager for each plate defined in the psyscript config.yaml, see readme
    global managers
    appConf = { "friendly_name": "Mudroom Plate",
                "plate_name": "mudroom_plate",
                "resolution_x": 240,
                "resolution_y": 320
                }
    apps = []
    apps.append(appConf)

    for appConf in apps:
        name = appConf["friendly_name"]
        plateName = appConf["plate_name"]
        resolution = (appConf["resolution_x"], appConf["resolution_y"])
        log.info(f"Creating Hasp Manager for '{plateName}'")

        manager = HaspManager(name, plateName, resolution)
        managers.append(manager)
        log.info('SCRIPT START EVENT SEND DESIGN')
        manager.sendDesign()
