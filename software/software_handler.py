############################
# **** IMPORT SECTION **** #
############################
import sys
import os
import linuxcnc

from PyQt5 import QtCore, QtWidgets

from qtvcp.widgets.mdi_line import MDILine as MDI_WIDGET
from qtvcp.widgets.mdi_history import MDIHistory as MDI_HISTORY
from qtvcp.widgets.gcode_editor import GcodeEditor as GCODE

from qtvcp.lib.keybindings import Keylookup
from qtvcp.core import Status, Action

# Set up logging
from qtvcp import logger
LOG = logger.getLogger(__name__)

# Mode mapping
MODE_MAP = {
    linuxcnc.MODE_MANUAL: "JOG",
    linuxcnc.MODE_AUTO: "AUTO",
    linuxcnc.MODE_MDI: "MDI"
}

# Set the log level for this module
#LOG.setLevel(logger.INFO) # One of DEBUG, INFO, WARNING, ERROR, CRITICAL

###########################################
# **** INSTANTIATE LIBRARIES SECTION **** #
###########################################

KEYBIND = Keylookup()
STATUS = Status()
ACTION = Action()

stat = linuxcnc.stat()
comm = linuxcnc.command()

###################################
# **** HANDLER CLASS SECTION **** #
###################################

class HandlerClass:

    ########################
    # **** INITIALIZE **** #
    ########################
    # widgets allows access to  widgets from the QtVCP files
    # at this point the widgets and hal pins are not instantiated
    def __init__(self, halcomp,widgets,paths):
        self.hal = halcomp
        self.w = widgets
        self.PATHS = paths

    ##########################################
    # SPECIAL FUNCTIONS SECTION              #
    ##########################################

    # at this point:
    # the widgets are instantiated.
    # the HAL pins are built but HAL is not set ready
    # This is where you make HAL pins or initialize state of widgets etc
    def initialized__(self):

        comm.state(linuxcnc.STATE_ESTOP_RESET)
        comm.wait_complete(10)

        comm.state(linuxcnc.STATE_ON)               # Set initial state to IDLE
        comm.wait_complete(10)

        comm.home(-1)  # Start homing Z-axis
        comm.wait_complete(60)

        STATUS.connect('mode-manual', lambda w: self.on_mode_manual())
        STATUS.connect('mode-mdi', lambda w: self.on_mode_mdi())
        STATUS.connect('mode-auto', lambda w: self.on_mode_auto())

        comm.mode(linuxcnc.MODE_AUTO)

        # Set up timer to update current mode every 200ms
        self.mode_timer = QtCore.QTimer()
        self.mode_timer.timeout.connect(self.timer_function)
        self.mode_timer.start(200)

        self.w.statuslabel_2.setText(f"STARTED")  

    def processed_key_event__(self,receiver,event,is_pressed,key,code,shift,cntrl):
        # when typing in MDI, we don't want keybinding to call functions
        # so we catch and process the events directly.
        # We do want ESC, F1 and F2 to call keybinding functions though
        if code not in(QtCore.Qt.Key_Escape,QtCore.Qt.Key_F1 ,QtCore.Qt.Key_F2,
                    QtCore.Qt.Key_F3,QtCore.Qt.Key_F5,QtCore.Qt.Key_F5):

            # search for the top widget of whatever widget received the event
            # then check if it is one we want the keypress events to go to
            flag = False
            receiver2 = receiver
            while receiver2 is not None and not flag:
                if isinstance(receiver2, QtWidgets.QDialog):
                    flag = True
                    break
                if isinstance(receiver2, MDI_WIDGET):
                    flag = True
                    break
                if isinstance(receiver2, GCODE):
                    flag = True
                    break
                receiver2 = receiver2.parent()

            if flag:
                if isinstance(receiver2, GCODE):
                    # if in manual do our keybindings - otherwise
                    # send events to G-code widget
                    if STATUS.is_man_mode() == False:
                        if is_pressed:
                            receiver.keyPressEvent(event)
                            event.accept()
                        return True
                elif is_pressed:
                    receiver.keyPressEvent(event)
                    event.accept()
                    return True
                else:
                    event.accept()
                    return True

        if event.isAutoRepeat():return True

        # ok if we got here then try keybindings
        try:
            return KEYBIND.call(self,event,is_pressed,shift,cntrl)
        except NameError as e:
            LOG.debug('Exception in KEYBINDING: {}'.format (e))
        except Exception as e:
            LOG.debug('Exception in KEYBINDING:', exc_info=e)
            print('Error in, or no function for: %s in handler file for-%s'%(KEYBIND.convert(event),key))
            return False

    ########################
    # CALLBACKS FROM STATUS #
    ########################

    #######################
    # CALLBACKS FROM FORM #
    #######################

    def tabChange(self, value):
        if value == 0:
            comm.mode(linuxcnc.MODE_AUTO)
        elif value == 2:
            comm.mode(linuxcnc.MODE_MANUAL)
        elif value == 3:
            comm.mode(linuxcnc.MODE_MDI)

    def gcodeEdit (self):

        self.w.stackedWidget.setCurrentIndex(1)

        current_dir = self.w.filemanager.getCurrentSelected()

        file = current_dir[0]
        
        # self.w.gcodeeditor.editMode()
        self.w.gcodeeditor.editor.setReadOnly(False)
        self.w.gcodeeditor.editor.load_text(file)

    def gcodeRead (self):

        self.w.stackedWidget.setCurrentIndex(0)

        current_dir = self.w.filemanager.getCurrentSelected()

        file = current_dir[0]

        saved = ACTION.SAVE_PROGRAM(self.w.gcodeeditor.editor.text(), file)
        if saved is not None:
            LOG.debug(f"File Saved: {file}")

            # self.w.gcodeeditor.readMode()
            self.w.gcodeeditor.editor.setReadOnly(True)

    #####################
    # GENERAL FUNCTIONS #
    #####################

    # Update current mode display every 200ms
    def timer_function(self):
        
        if STATUS.is_auto_running():
            self.w.statuslabel_2.setText(f"PROGRAM RUNNING") 

            self.w.tabwidget.setTabEnabled(1, False)  # EDIT
            self.w.tabwidget.setTabEnabled(2, False)  # JOG
            self.w.tabwidget.setTabEnabled(3, False)  # MDI

        elif STATUS.is_auto_paused():
            self.w.statuslabel_2.setText(f"PROGRAM PAUSED")
        else:
            self.w.statuslabel_2.setText(f"IDLE")
            
            self.w.tabwidget.setTabEnabled(1, True)  # EDIT
            self.w.tabwidget.setTabEnabled(2, True)  # JOG
            self.w.tabwidget.setTabEnabled(3, True)  # MDI

    def on_mode_manual(self):
        self.w.statuslabel.setText(f"JOG") 

    def on_mode_auto(self):
        self.w.statuslabel.setText(f"AUTO") 

    def on_mode_mdi(self):
        self.w.statuslabel.setText(f"MDI") 

    # keyboard jogging from key binding calls
    # double the rate if fast is true
    def kb_jog(self, state, joint, direction, fast = False, linear = True):
        if not STATUS.is_man_mode() or not STATUS.machine_is_on():
            return
        if linear:
            distance = STATUS.get_jog_increment()
            rate = STATUS.get_jograte()/60
        else:
            distance = STATUS.get_jog_increment_angular()
            rate = STATUS.get_jograte_angular()/60
        if state:
            if fast:
                rate = rate * 2
            ACTION.JOG(joint, direction, rate, distance)
        else:
            ACTION.JOG(joint, 0, 0, 0)

    #####################
    # KEY BINDING CALLS #
    #####################

    # Machine control
    def on_keycall_ESTOP(self,event,state,shift,cntrl):
        if state:
            ACTION.SET_ESTOP_STATE(STATUS.estop_is_clear())
    def on_keycall_POWER(self,event,state,shift,cntrl):
        if state:
            ACTION.SET_MACHINE_STATE(not STATUS.machine_is_on())
    def on_keycall_HOME(self,event,state,shift,cntrl):
        if state:
            if STATUS.is_all_homed():
                ACTION.SET_MACHINE_UNHOMED(-1)
            else:
                ACTION.SET_MACHINE_HOMING(-1)
    def on_keycall_ABORT(self,event,state,shift,cntrl):
        if state:
            if STATUS.stat.interp_state == linuxcnc.INTERP_IDLE:
                self.w.close()
            else:
                self.cmnd.abort()

    # Linear Jogging
    def on_keycall_XPOS(self,event,state,shift,cntrl):
        self.kb_jog(state, 0, 1, shift)

    def on_keycall_XNEG(self,event,state,shift,cntrl):
        self.kb_jog(state, 0, -1, shift)

    def on_keycall_YPOS(self,event,state,shift,cntrl):
        self.kb_jog(state, 1, 1, shift)

    def on_keycall_YNEG(self,event,state,shift,cntrl):
        self.kb_jog(state, 1, -1, shift)

    def on_keycall_ZPOS(self,event,state,shift,cntrl):
        self.kb_jog(state, 2, 1, shift)

    def on_keycall_ZNEG(self,event,state,shift,cntrl):
        self.kb_jog(state, 2, -1, shift)

    def on_keycall_APOS(self,event,state,shift,cntrl):
        pass
        #self.kb_jog(state, 3, 1, shift, False)

    def on_keycall_ANEG(self,event,state,shift,cntrl):
        pass
        #self.kb_jog(state, 3, -1, shift, linear=False)

    ###########################
    # **** closing event **** #
    ###########################

    def closing_cleanup__(self):
        # Stop the mode update timer
        if hasattr(self, 'mode_timer'):
            self.mode_timer.stop()

    ##############################
    # required class boiler code #
    ##############################

    def __getitem__(self, item):
        return getattr(self, item)
    def __setitem__(self, item, value):
        return setattr(self, item, value)

################################
# required handler boiler code #
################################

def get_handlers(halcomp,widgets,paths):
     return [HandlerClass(halcomp,widgets,paths)]