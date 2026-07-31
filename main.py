import os
import urllib.parse
import requests
from io import BytesIO
from PIL import Image as PILImage

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.core.image import Image as CoreImage

class SaveFolderDialog(BoxLayout):
    def __init__(self, save_callback, cancel_callback, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        default_path = os.path.expanduser('~')
        if os.path.exists('/sdcard'):
            default_path = '/sdcard'

        self.filechooser = FileChooserListView(path=default_path, dirselect=True)
        self.add_widget(self.filechooser)
        
        btn_layout = BoxLayout(size_hint_y=None, height='48dp', spacing=10)
        cancel_btn = Button(text="Cancel", on_release=lambda x: cancel_callback())
        save_btn = Button(text="Save Here", on_release=lambda x: save_callback(self.filechooser.path))
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(save_btn)
        self.add_widget(btn_layout)

class StudyApp(App):
    def build(self):
        self.temp_image_data = None
        
        root = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        # Header Title
        header = Label(
            text="Free AI Image Generator & Study Companion",
            size_hint_y=None,
            height='35dp',
            bold=True
        )
        root.add_widget(header)
        
        # Scrollable Chat Area
        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.scroll.add_widget(self.chat_layout)
        root.add_widget(self.scroll)
        
        # Bottom Controls Layout
        bottom_box = BoxLayout(orientation='vertical', size_hint_y=None, height='90dp', spacing=5)
        
        # TTS Voice Switch Row
        toggle_row = BoxLayout(size_hint_y=None, height='30dp', spacing=10)
        toggle_row.add_widget(Label(text="TTS Voice:", size_hint_x=None, width='90dp'))
        self.voice_switch = Switch(active=True)
        toggle_row.add_widget(self.voice_switch)
        bottom_box.add_widget(toggle_row)
        
        # Text Input & Generate Button Row
        input_row = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        self.user_input = TextInput(hint_text="Enter image prompt (e.g. human heart diagram)...", multiline=False)
        send_btn = Button(text="Generate", size_hint_x=None, width='90dp', on_release=self.on_send)
        
        input_row.add_widget(self.user_input)
        input_row.add_widget(send_btn)
        bottom_box.add_widget(input_row)
        
        root.add_widget(bottom_box)
        return root

    def add_message(self, text, is_user=False):
        lbl = Label(
            text=f"{'You' if is_user else 'AI'}: {text}",
            size_hint_y=None,
            text_size=(self.scroll.width - 20, None),
            halign='left' if not is_user else 'right'
        )
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1] + 10))
        self.chat_layout.add_widget(lbl)

    def on_send(self, instance):
        text = self.user_input.text.strip()
        if not text:
            return
            
        self.add_message(text, is_user=True)
        self.user_input.text = ""
        
        # Trigger TTS Voice if enabled
        if self.voice_switch.active:
            self.speak_status(f"Generating image for {text}")
            
        self.generate_free_image(text)

    def speak_status(self, text):
        # Stub hook for your compiled Piper TTS binary
        pass

    def generate_free_image(self, prompt):
        self.add_message("Generating 100% Free AI image...", is_user=False)
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            # Free API Endpoint (Pollinations AI)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
            
            res = requests.get(url, timeout=25)
            if res.status_code == 200:
                self.temp_image_data = res.content
                
                # Render inside Kivy layout
                im = PILImage.open(BytesIO(res.content))
                byte_io = BytesIO()
                im.save(byte_io, format='png')
                byte_io.seek(0)
                
                core_img = CoreImage(byte_io, ext='png')
                img_widget = KivyImage(texture=core_img.texture, size_hint_y=None, height='260dp')
                
                # Folder Selection Button
                save_btn = Button(
                    text="Save Image to Chosen Folder",
                    size_hint_y=None,
                    height='42dp',
                    on_release=lambda x: self.open_folder_picker()
                )
                
                img_container = BoxLayout(orientation='vertical', size_hint_y=None, height='310dp', spacing=5)
                img_container.add_widget(img_widget)
                img_container.add_widget(save_btn)
                
                self.chat_layout.add_widget(img_container)
            else:
                self.add_message("Failed to fetch image from free server.", is_user=False)
        except Exception as e:
            self.add_message(f"Generation Error: {str(e)}", is_user=False)

    def open_folder_picker(self):
        content = SaveFolderDialog(
            save_callback=self.save_image_to_path,
            cancel_callback=self.dismiss_popup
        )
        self._popup = Popup(title="Select Save Directory", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def dismiss_popup(self):
        if hasattr(self, '_popup'):
            self._popup.dismiss()

    def save_image_to_path(self, target_folder):
        self.dismiss_popup()
        if not self.temp_image_data:
            return
            
        try:
            filename = f"ai_img_{int(os.urandom(4).hex(), 16)}.png"
            full_path = os.path.join(target_folder, filename)
            
            with open(full_path, 'wb') as f:
                f.write(self.temp_image_data)
                
            self.add_message(f"Image saved to folder: {full_path}", is_user=False)
        except Exception as e:
            self.add_message(f"Save error: {str(e)}", is_user=False)

if __name__ == '__main__':
    StudyApp().run()
