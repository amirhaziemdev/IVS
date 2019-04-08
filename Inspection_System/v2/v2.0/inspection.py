"""
Created by: Ahmad Ammar Asyraaf Bin Jainuddin
Version: 2.0.0-08042019
Last Modified: 11:26 AM - 08/04/2019

"""
from kivy.config import Config
import imutils
# Config.set('graphics', 'resizable', '0') # 0 being off 1 being on as in true/false
# Min width and height should be change according to screen spec.
# Changes should also be made within kv file
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '600')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
import cv2
import numpy as np
import os
import shutil
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior 
from kivy.factory import Factory
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
import json
from kivy.uix.popup import Popup

class SLabel(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(SLabel, self).__init__(**kwargs)
        
class SBox(BoxLayout, Button):
    def __init__(self, **kwargs):
        super(SBox, self).__init__(**kwargs)
            
class HoverBehavior(object):
    hovered = BooleanProperty(False)
    border_point= ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type("on_enter")
        self.register_event_type("on_leave")
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return # do proceed if I"m not displayed <=> If have no parent
        pos = args[1]
        #Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            #We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch("on_enter")
        else:
            self.dispatch("on_leave")

    def on_enter(self):
        pass

    def on_leave(self):
        pass
        
class SM(ScreenManager):
    settings = open("./settings.json", "r").read()
    settings = json.loads(settings)
    camera = settings["Settings"]["Camera"]
    
    def __init__(self, **kwargs):
        super(SM, self).__init__(**kwargs)
        self.app = App.get_running_app()
        
        # Boot up sequence
        Clock.schedule_once(self.start_up, 0)
    
    # Main Functions
    def start_up(self, dt):
        self.ids.console.text += "[   System   ]  System is starting up!"
        self.ids.console2.text += "[   System   ]  System is starting up!"
        try:
            self.import_settings()
            self.console_write("Importing settings!")
        except:
            raise ValueError("Settings file doesnt exist")
        
        try:
            self.feature_listing()
            self.console_write("Detection system is running!")
        except:
            raise ValueError("Feature listing not found!")
        
    def import_settings(self):
        settings = open("./settings.json", "r").read()
        settings = json.loads(settings)
        self.app.root.ids.threshold_value.value = settings["Settings"]["Threshold"]
    
    def feature_listing(self):
        count = 0
        file = open("./feature_list.txt", "r")
        feature = file.read().split("\n") # Current feature list
        for each in feature:
            if each == "":
                break
            new_box = SBox()
            new_box.id = each
            new_box.orientation = "horizontal"
            new_box.size_hint = (1, .1)
            new_checkbox = CheckBox()
            new_checkbox.id = each
            new_checkbox.size_hint = (.05, 1)
            new_checkbox.group = "feature"
            new_checkbox.bind(on_press=self.change_detection)
            new_box.add_widget(new_checkbox)
            new_label = SLabel()
            new_label.id = each
            new_label.text = each
            new_label.bind(on_press=self.change_detection)
            new_label.size_hint = (.95, 1)
            new_box.add_widget(new_label)
            self.ids.holder.add_widget(new_box)
            if each == KivyCamera.feature_detect:
                new_box.background_color = (0.5, 0.5, 0.5, 1)
                new_checkbox.active = True
            count+=1
        rh = (10-count)/10
        space_box = BoxLayout()
        space_box.size_hint = (1, rh)
        self.ids.holder.add_widget(space_box)
        file.close()
    
    def update_feature_listing(self):
        limit = len(self.ids.holder.children)
        i = 0
        while i < limit:
            self.ids.holder.remove_widget(self.ids.holder.children[0])
            i+=1
        self.feature_listing()
            
    # Changing Feature Detect Function
    def change_detection(self, obj):
        self.app.root.ids.camera.change_feature(obj.id)
        self.update_feature_listing()
    
    # Changing screen Function
    def change_page(self):
        if self.ids.main_page.manager.current == "settings_page":
            KivyCamera.isDetecting = True
            self.ids.main_page.manager.current = "main_page"
            return
        KivyCamera.isDetecting = False
        self.ids.main_page.manager.current = "settings_page"
    
    # Console Function  
    def console_write(self, text):
        self.ids.console.text += "\n[   System   ]  " + text
        self.ids.scroller.scroll_to(self.ids.console) # For autoscrolling
        self.ids.console2.text += "\n[   System   ]  " + text
        self.ids.scroller2.scroll_to(self.ids.console) # For autoscrolling
    
    # ON/OFF Button Function
    def cam_toggle(self):
        if KivyCamera.isDetecting == True:
            KivyCamera.isDetecting = False
            self.console_write("Feature Detection has been turned OFF!")
        else:
            KivyCamera.isDetecting = True
            self.console_write("Feature Detection has turned ON!")
    
    # Test Label Functions
    def test_go(self):
        self.ids.test_label.background_color=(0.0, 0.5, 0.0, 1)
        self.ids.test_label.text = "OKAY!"
    
    def test_ng(self):
        self.ids.test_label.background_color=(0.5, 0.0, 0.0, 1)
        self.ids.test_label.text = "NOT OKAY!"
        
    # Next Button Function
    def next(self):
        file = open("./feature_list.txt", "r")
        feature = file.read().split("\n")
        file.close()
        for each in feature:
            if each == KivyCamera.feature_detect:
                get = feature.index(each)
        if feature[get+1] == "":
            get = 0
        else:
            get+=1
        self.app.root.ids.camera.change_feature(feature[get])
        self.update_feature_listing()
        
    # RESET Button Functions
    def reset(self):
        feature = open("./feature_list.txt", "w")
        feature.write("feature1\nfeature2\n")
        feature.close()
        feature = open("./feature_list.txt", "r").read().split("\n")
        KivyCamera.feature_detect = feature[0]
        
        shutil.rmtree(f"template")
        self.copytree("./data","./template")
        self.console_write("DATA RESET!!!")
        self.update_feature_listing()
        
    def copytree(self, src, dst, symlinks = False, ignore = None):
        if not os.path.exists(dst):
            os.makedirs(dst)
            shutil.copystat(src, dst)
        lst = os.listdir(src)
        if ignore:
            excl = ignore(src, lst)
            lst = [x for x in lst if x not in excl]
        for item in lst:
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if symlinks and os.path.islink(s):
                if os.path.lexists(d):
                    os.remove(d)
                os.symlink(os.readlink(s), d)
                try:
                    st = os.lstat(s)
                    mode = stat.S_IMODE(st.st_mode)
                    os.lchmod(d, mode)
                except:
                    pass # lchmod not available
            elif os.path.isdir(s):
                self.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

class KivyCamera(Image):
    isDetecting =  True # KivyCamera attribute for start/stop cam feed
    feature = open("./feature_list.txt", "r").read().split("\n") # Current feature list
    feature_detect = feature[0] # For detection on camera
    
    def __init__(self, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.app = App.get_running_app()
        
        # Select external cam and get fps
        try:
            self.capture = cv2.VideoCapture(SM.camera)
            self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        except:
            raise ValueError("No camera found!")
        
        # Set refresh rate
        Clock.schedule_interval(self.update, 1/self.fps)

    def snap(self):
        ret, frame = self.capture.read()
        h, w = frame.shape[:2]
        return ret, frame, h, w

    def update(self, dt):
        ret, frame, _, _2 = self.snap()
        
        if ret:
            # Do feature detection
            if self.isDetecting == True:
                frame = self.feature_detection(frame)
                
            rectangle_bgr = (0, 0, 0)
            # set some text
            text = f"{KivyCamera.feature_detect}"
            # get the width and height of the text box
            (text_width, text_height) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, thickness=3)[0]
            # set the text start position
            text_offset_x = 10
            text_offset_y = 30
            # make the coords of the box with a small padding of two pixels
            box_coords = ((text_offset_x-5, text_offset_y+5), (text_offset_x+text_width-5, text_offset_y-text_height-5))
            cv2.rectangle(frame, box_coords[0], box_coords[1], rectangle_bgr, cv2.FILLED)
            cv2.putText(frame, text, (text_offset_x, text_offset_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

            # Convert it to texture for display in Kivy GUI
            frame = cv2.flip(frame, 0) # Flip v
            w, h = int(self.width), int(self.height)
            frame = cv2.resize(frame, (w,h))
            buf = frame.tostring()
            image_texture = Texture.create(
                size=(w, h), colorfmt="bgr")
            image_texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
            # display image from the texture
            self.texture = image_texture
            
    def cv2_select_roi(self):
        # Get untouched frame for ROI selection
        ret, im, _, _2 = self.snap()
        
        # Get feature name and template image listing
        feature = KivyCamera.feature_detect
        dir = f"./template/{feature}/"

        # Check if feature directory exist, Create new if doesn't
        try:
            template_list = os.listdir(dir)
        except:
            os.mkdir(dir)
            template_list = False

        # Get latest filename. if empty start from 1
        if not template_list:
            template_list = [0]
        else:
            template_list = template_list[-1].split(".jpg")
        next = int(template_list[0])+1
        
        if next != 1:
            self.app.root.console_write("Image can only be captured once!")
            return
        
        # Text for console
        success1 = f"Image for {feature} has been captured successfully!"
        unsuccessful = "Image captured unsuccessful! Cannot capture whole image!"
        
        # Get user input on ROI
        r = cv2.selectROI("Select Region of Interest", im, False)
        
        # Write image if ROI is given, else return unsuccessful
        if r[1]:
            imCrop = im[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
            cv2.imwrite(dir+str(next)+'.jpg', imCrop)
            self.app.root.console_write(success1)
        else:
            self.app.root.console_write(unsuccessful)
        cv2.destroyAllWindows()
    
    def feature_detection(self, frame): # Using template matching
        good = 0
        # Get frame and change to gray
        img_bgr = frame
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Get feature name and template image listing
        feature = KivyCamera.feature_detect
        dir = f"./template/{feature}/"
        
        # Check if feature directory exist, Create new if doesn't
        try:
            template_list = os.listdir(dir)
        except:
            try:
                os.mkdir(dir)
            except:
                pass
            template_list = False
        
        # If listing is empty return back frame
        if not template_list:
            return img_bgr
        
        # Foreach image in feature dir do template matching with frame
        for img in template_list:
            template = cv2.imread(str(dir+img), 0)
            h,w = template.shape[0:2]
            
            res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            # Threshold for template matching can be control within GUI (default:0.8)
            threshold = self.app.root.ids.threshold_value.value
            loc = np.where(res>=threshold)
            if loc[0].any():
                good+=1
            
            # Draw on frame the matching region
            for pt in zip(*loc[::-1]):
                cv2.rectangle(img_bgr, pt, (pt[0]+w, pt[1]+h), (0,255,255), 1)
        
        # Kivy GUI manipulation for if there is a match
        if good > 0:
            self.app.root.test_go()
        else:
            self.app.root.test_ng()
                
        return img_bgr
    
    def change_feature(self, fname):
        dir = f"./template/{fname}"
        template_list = os.listdir(dir)
        if not template_list:
            self.app.root.console_write(f"No template image has been captured yet for {fname}!")
        KivyCamera.feature_detect = fname

class AddFPopup(Popup):
    def __init__(self, **kwargs):
        super(AddFPopup, self).__init__(**kwargs)
        self.app = App.get_running_app()
        
    def on_open(self):
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.run = 0
        
    def _keyboard_closed(self):
        pass
        
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.ids.feature_name.focus = False
        if keycode[1] == "enter" and self.run == 0:
            self.add_feature()
            self.ids.feature_name.text = ""
            self.run = 1
            return
        if (97 <= keycode[0] <= 122) or (48 <= keycode[0] <= 57):
            self.ids.feature_name.text += keycode[1]
        elif keycode[0] == 8:
            self.ids.feature_name.text = self.ids.feature_name.text[:-1]
        else:
            pass
            
    def on_dismiss(self):
        self._keyboard.unbind()
        self._keyboard = None
        self.run = 0
    
    def add_feature(self):
        self.dismiss()
        feature = open("./feature_list.txt", "r")
        list = feature.read().split("\n")
        text = self.ids.feature_name.text
        for each in list:
            if text == "":
                self.app.root.console_write(f"Invalid name!")
                return
            elif text == each:
                self.app.root.console_write(f"{text} already exist!")
                return
        feature.close()
        feature = open("./feature_list.txt", "a")
        feature.write(text+"\n")
        feature.close()
        self.app.root.console_write(f"{text} has been added!")
        self.app.root.console_write(f"Please capture an image once to start detection!")
        KivyCamera.feature_detect = text
        try:
            dir = f"./template/{text}"
            os.makedirs(dir)
        except:
            pass
        self.app.root.update_feature_listing()
        
class DelFPopup(Popup):
    def __init__(self, **kwargs):
        super(DelFPopup, self).__init__(**kwargs)
        self.app = App.get_running_app()
        
    def del_feature(self):
        self.dismiss()
        feature = KivyCamera.feature_detect
        file = open("./feature_list.txt", "r")
        list = file.read().split("\n") # Current feature list
        file.close()
        if len(list) == 2:
            self.app.root.console_write(f"Cannot remove the last feature!")
            return
        list.remove(feature)
        file = open("./feature_list.txt", "w")
        for each in list:
            if each == "":
                break
            file.write(each+"\n")
        file.close()
        list = open("./feature_list.txt", "r").read().split("\n") # Current feature list
        KivyCamera.feature_detect = list[0]
        shutil.rmtree(f"./template/{feature}")
        self.app.root.console_write(f"{feature} has been removed!")
        self.app.root.update_feature_listing()
        
class SelectROI(Popup):
    def __init__(self, **kwargs):
        super(SelectROI, self).__init__(**kwargs)
        self.app = App.get_running_app()
        
    def on_open(self):
        self.ids.image.get_image()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.run = 0
        Clock.schedule_interval(self.ids.image.update, 0)
        
    def on_dismiss(self):
        Clock.unschedule(self.ids.image.update)
        self._keyboard.unbind()
        self._keyboard = None
        self.run = 0
        
    def _keyboard_closed(self):
        pass
        
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == "enter" and self.run == 0:
            self.dismiss()
            self.ids.image.confirm()
            self.run = 1
            return

class SelectROIImage(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(SelectROIImage, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.first = 0
        self.second = 0
        self.point1 = []
        self.point2 = []
        self.copy = np.zeros((self.height,self.width,3), np.uint8)
        
    def get_image(self):
        self.ret, self.frame, self.h, self.w = self.app.root.ids.camera.snap()
        self.frame = cv2.flip(self.frame, 0) # Flip v
        self.copy = self.frame
        
    def update(self, dt):
        w, h = int(self.width), int(self.height)
        self.frame = cv2.resize(self.frame, (w,h))
        buf = self.frame.tostring()
        image_texture = Texture.create(
            size=(w, h), colorfmt="bgr")
        image_texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
        # display image from the texture
        self.texture = image_texture
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.second == 0:
            self.frame = self.copy
            self.point1 = tuple(int(round(touch.pos[i] - self.pos[i], 0)) for i in range(2))
            self.first = 1
            self.second = 1
    
    def on_touch_move(self, touch):
        self.frame = self.copy
        w, h = int(self.width), int(self.height)
        self.frame = cv2.resize(self.copy, (w,h))
        if self.collide_point(*touch.pos) and self.first == 1:
            self.point3 = tuple(int(round(touch.pos[i] - self.pos[i], 0)) for i in range(2))
            cv2.rectangle(self.frame, self.point3, self.point1, (0,255,0), 5)
        
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.first == 1:
            self.point2 = tuple(int(round(touch.pos[i] - self.pos[i], 0)) for i in range(2))
            cv2.rectangle(self.frame, self.point2, self.point1, (0,255,0), 5)
        self.first = 0
        self.second = 0
        
    def check_point(self):
        list = []
        if self.point2[1] > self.point1[1]:
            list.append(self.point1[1])
            list.append(self.point2[1])
        else:
            list.append(self.point2[1])
            list.append(self.point1[1])
        if self.point2[0] > self.point1[0]:
            list.append(self.point1[0])
            list.append(self.point2[0])
        else:
            list.append(self.point2[0])
            list.append(self.point1[0])
        return list
        
    def confirm(self):
        # Get feature name and template image listing
        feature = KivyCamera.feature_detect
        dir = f"./template/{feature}/"

        # Check if feature directory exist, Create new if doesn't
        try:
            template_list = os.listdir(dir)
        except:
            try:
                os.mkdir(dir)
            except:
                pass
            template_list = False

        # Get latest filename. if empty start from 1
        if not template_list:
            template_list = [0]
        else:
            template_list = template_list[-1].split(".jpg")
        next = int(template_list[0])+1
        
        if next != 1:
            self.app.root.console_write("Image can only be captured once!")
            return
        
        # Text for console
        success1 = f"Image for {feature} has been captured successfully!"
        unsuccessful = "Image captured unsuccessful! Cannot capture whole image!"
        
        if self.point1 and self.point2:
            r = self.check_point()
            w, h = int(self.width), int(self.height)
            self.copy = cv2.resize(self.copy, (w,h))
            imCrop = self.copy[r[0]:r[1], r[2]:r[3]]
            imCrop = cv2.flip(imCrop, 0) # Flip v
            cv2.imwrite(dir+str(next)+'.jpg', imCrop)
            self.app.root.console_write(success1)
        else:
            self.app.root.console_write(unsuccessful)
        
class GenericButton(Button, HoverBehavior):  
    def on_enter(self):
        self.background_color=(0.5, 0.5, 0.5, 1)
    def on_leave(self):
        self.background_color=(0.3, 0.3, 0.3, 1)
        
class RedButton(Button, HoverBehavior):
    def on_enter(self):
        self.background_color=(1.0, 0.3, 0.3, 1)
    def on_leave(self):
        self.background_color=(1.0, 0.1, 0.1, 1)
        
class ThresholdSlider(Slider):
    def __init__(self, **kwargs):
        super(ThresholdSlider, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.run = 0
    
    # self.run is used caused somehow this function run twice!!
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.run == 0:
            self.value = round(self.value, 2)
            self.app.root.console_write(f"Threshold value has been changed to {self.value}")
            settings = open("./settings.json", "r").read()
            settings = json.loads(settings)
            settings["Settings"]["Threshold"] = self.value
            with open("./settings.json", "w") as outfile:
                json.dump(settings, outfile, indent=4, ensure_ascii=False)
            self.run+=1
        else:
            self.run = 0
    
class InspectionApp(App):
    def on_start(self):
          Window.bind(on_key_down=self.on_key_down)
          
    def on_key_down(self, win, key, scancode, string, modifiers):
        if key == 292:
            Window.toggle_fullscreen()
            return True
    
    def build(self):
        self.title = "TXMR Inspection System V1.1.6"
        self.icon = "./icon.png"
        Factory.register("HoverBehavior", HoverBehavior)
        return SM()

if __name__ == "__main__":
    InspectionApp().run()