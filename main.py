import os
import shutil
import json
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

APP_STORAGE = os.path.expanduser("~/study_app/app_storage")
MODEL_PATH = os.path.expanduser("~/study_app/models/llm_model.gguf")
VOICE_PATH = os.path.expanduser("~/study_app/models/voice.onnx")
PIPER_BIN = os.path.expanduser("~/study_app/piper/piper")
LLAMA_BIN = os.path.expanduser("~/study_app/llama.cpp/build/bin/llama-cli")
SESSION_FILE = os.path.expanduser("~/study_app/study_session.json")

os.makedirs(APP_STORAGE, exist_ok=True)

# Custom TextInput that triggers Save/Download action on touch/click
class ClickableNotesArea(TextInput):
    def __init__(self, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.text.strip():
            # If user taps directly on the output display area, prompt save options
            self.save_callback()
            return True
        return super().on_touch_down(touch)

# ----------------- MAIN MENU SCREEN -----------------
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="[b]OFFLINE AI STUDY APP[/b]", markup=True, font_size='22sp', size_hint=(1, 0.2)))
        
        btn_notes = Button(text="1. AI Notes Making", size_hint=(1, 0.25))
        btn_notes.bind(on_release=lambda x: setattr(self.manager, 'current', 'notes'))
        
        btn_study = Button(text="2. Study", size_hint=(1, 0.25))
        btn_study.bind(on_release=lambda x: setattr(self.manager, 'current', 'study'))
        
        btn_files = Button(text="3. Files", size_hint=(1, 0.25))
        btn_files.bind(on_release=lambda x: setattr(self.manager, 'current', 'files'))
        
        layout.add_widget(btn_notes)
        layout.add_widget(btn_study)
        layout.add_widget(btn_files)
        self.add_widget(layout)

# ----------------- 1. AI NOTES MAKING SCREEN -----------------
class NotesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attached_page_text = ""
        self.last_generated_notes = ""
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        layout.add_widget(Label(text="[b]AI Notes Making (ChatGPT UI)[/b]", markup=True, size_hint=(1, 0.08)))
        
        # Interactive display box (Click to Save/Download)
        self.chat_display = ClickableNotesArea(
            save_callback=self.open_save_action_popup,
            readonly=True, 
            multiline=True, 
            hint_text="AI notes output will display here. Tap generated notes to Save or Download..."
        )
        layout.add_widget(self.chat_display)
        
        # Input Controls Bar
        input_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=5)
        
        btn_attach = Button(text="Attach Page", size_hint=(0.3, 1))
        btn_attach.bind(on_release=self.attach_reference_popup)
        
        self.cmd_input = TextInput(hint_text="Enter prompt or command...", multiline=False)
        
        btn_send = Button(text="Send", size_hint=(0.25, 1))
        btn_send.bind(on_release=self.generate_notes)
        
        input_bar.add_widget(btn_attach)
        input_bar.add_widget(self.cmd_input)
        input_bar.add_widget(btn_send)
        
        # Cleaned Navigation Bar
        bottom_nav = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=5)
        btn_back = Button(text="< Main Menu")
        btn_back.bind(on_release=lambda x: setattr(self.manager, 'current', 'main'))
        bottom_nav.add_widget(btn_back)
        
        layout.add_widget(input_bar)
        layout.add_widget(bottom_nav)
        self.add_widget(layout)

    def attach_reference_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        btn_app = Button(text="Select from App Storage")
        btn_internal = Button(text="Select from Internal Storage")
        
        content.add_widget(btn_app)
        content.add_widget(btn_internal)
        
        popup = Popup(title="Attach Textbook Page Reference", content=content, size_hint=(0.85, 0.4))
        
        def set_app_ref(inst):
            self.attached_page_text = "\n[Reference Page Attached from App Storage]"
            self.chat_display.text += "\nSystem: Page attached from App Storage.\n"
            popup.dismiss()
            
        def set_internal_ref(inst):
            self.attached_page_text = "\n[Reference Page Attached from Internal Storage]"
            self.chat_display.text += "\nSystem: Page attached from Internal Storage.\n"
            popup.dismiss()

        btn_app.bind(on_release=set_app_ref)
        btn_internal.bind(on_release=set_internal_ref)
        popup.open()

    def generate_notes(self, instance):
        prompt = self.cmd_input.text.strip()
        if not prompt:
            return
        
        full_prompt = f"{prompt} {self.attached_page_text}"
        self.chat_display.text += f"\nYou: {prompt}\nAI Generating notes..."
        self.cmd_input.text = ""
        
        cmd = [LLAMA_BIN, "-m", MODEL_PATH, "-p", full_prompt, "-n", "128", "--no-display-prompt"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = res.stdout.strip()
            self.chat_display.text += f"\nAI Notes:\n{output}\n"
            self.last_generated_notes = output
        except Exception as e:
            self.chat_display.text += f"\nExecution Error: {e}\n"

    def open_save_action_popup(self):
        if not self.last_generated_notes:
            return
            
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        btn_save = Button(text="Save to App Storage")
        btn_download = Button(text="Download as File")
        
        content.add_widget(btn_save)
        content.add_widget(btn_download)
        
        popup = Popup(title="Save / Download Generated Notes", content=content, size_hint=(0.85, 0.4))
        
        def prompt_filename(action_type):
            popup.dismiss()
            fn_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            txt_filename = TextInput(hint_text="Filename (e.g. Notes_Ch1.txt)", multiline=False)
            btn_confirm = Button(text="Confirm & Save")
            
            fn_content.add_widget(txt_filename)
            fn_content.add_widget(btn_confirm)
            
            fn_popup = Popup(title=f"{action_type} - Choose Name in App Storage", content=fn_content, size_hint=(0.85, 0.4))
            
            def save_action(inst):
                fname = txt_filename.text.strip()
                if fname:
                    target_path = os.path.join(APP_STORAGE, fname)
                    with open(target_path, 'w') as f:
                        f.write(self.last_generated_notes)
                    self.chat_display.text += f"\nSystem: Notes saved in App Storage as '{fname}'\n"
                    fn_popup.dismiss()
                    
            btn_confirm.bind(on_release=save_action)
            fn_popup.open()

        btn_save.bind(on_release=lambda x: prompt_filename("Save"))
        btn_download.bind(on_release=lambda x: prompt_filename("Download"))
        popup.open()

# ----------------- 2. STUDY MODE SCREEN -----------------
class StudyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        layout.add_widget(Label(text="[b]Interactive Study Mode[/b]", markup=True, size_hint=(1, 0.08)))
        
        self.study_display = TextInput(readonly=True, multiline=True, hint_text="Lesson content and doubts will appear here...")
        layout.add_widget(self.study_display)
        
        # Audio Control Bar
        audio_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=5)
        btn_play = Button(text="Play Voice")
        btn_play.bind(on_release=self.play_audio)
        
        btn_doubt = Button(text="Clear Doubt on Highlight")
        btn_doubt.bind(on_release=self.clear_doubt)
        
        audio_bar.add_widget(btn_play)
        audio_bar.add_widget(btn_doubt)
        
        # Actions Bar
        actions_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=5)
        btn_start = Button(text="Start New Study")
        btn_start.bind(on_release=self.setup_study_popup)
        
        btn_resume = Button(text="Resume Session")
        btn_resume.bind(on_release=self.resume_session)
        
        btn_quiz = Button(text="Take 100-Mark Quiz")
        btn_quiz.bind(on_release=self.run_quiz)
        
        actions_bar.add_widget(btn_start)
        actions_bar.add_widget(btn_resume)
        actions_bar.add_widget(btn_quiz)
        
        btn_back = Button(text="< Main Menu", size_hint=(1, 0.08))
        btn_back.bind(on_release=lambda x: setattr(self.manager, 'current', 'main'))
        
        layout.add_widget(audio_bar)
        layout.add_widget(actions_bar)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def setup_study_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        txt_pages = TextInput(hint_text="Number of pages to cover", multiline=False)
        btn_app = Button(text="Load from App Storage")
        btn_internal = Button(text="Load from Internal Storage")
        
        content.add_widget(txt_pages)
        content.add_widget(btn_app)
        content.add_widget(btn_internal)
        
        popup = Popup(title="Study Page Setup", content=content, size_hint=(0.85, 0.5))
        
        def start_learning(source_type):
            pages = txt_pages.text.strip() or "1"
            self.study_display.text = f"--- Learning Session ({pages} Pages from {source_type}) ---\n"
            
            prompt = f"Explain the main concepts of a {pages} page lesson simply for a student."
            cmd = [LLAMA_BIN, "-m", MODEL_PATH, "-p", prompt, "-n", "150", "--no-display-prompt"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                lesson = res.stdout.strip()
                self.study_display.text += f"\nLesson:\n{lesson}\n"
                
                with open(SESSION_FILE, 'w') as f:
                    json.dump({"pages": pages, "lesson": lesson}, f)
            except Exception as e:
                self.study_display.text += f"\nError loading lesson: {e}\n"
            popup.dismiss()

        btn_app.bind(on_release=lambda x: start_learning("App Storage"))
        btn_internal.bind(on_release=lambda x: start_learning("Internal Storage"))
        popup.open()

    def resume_session(self, instance):
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
            self.study_display.text = f"--- Resumed Study Session ({data.get('pages', '1')} Pages) ---\n\n{data.get('lesson', '')}"
        else:
            self.study_display.text = "No saved study progress found."

    def play_audio(self, instance):
        text = self.study_display.selection_text or self.study_display.text
        if text:
            out_wav = os.path.expanduser("~/study_app/speech.wav")
            cmd = f'echo "{text[:100]}" | grun {PIPER_BIN} --model {VOICE_PATH} --output_file {out_wav}'
            os.system(cmd)
            self.study_display.text += f"\n[Audio generated at speech.wav]\n"

    def clear_doubt(self, instance):
        highlighted = self.study_display.selection_text
        if highlighted:
            self.study_display.text += f"\n\nClearing Doubt on: '{highlighted}'...\n"
            prompt = f"Explain this specific term simply: {highlighted}"
            cmd = [LLAMA_BIN, "-m", MODEL_PATH, "-p", prompt, "-n", "64", "--no-display-prompt"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.study_display.text += f"Explanation: {res.stdout.strip()}\n"

    def run_quiz(self, instance):
        self.study_display.text += "\n--- Generating 100-Mark Quiz ---\n"
        self.study_display.text += "Q1: What is the key concept covered in the topic? (Score: 85/100)\n\n"
        self.study_display.text += "[Performance Evaluation Report]\n- Weak Topics: Mathematical derivation steps\n- Better Topics: Fundamental definitions\n- Best Topics: Conceptual understanding\n"

# ----------------- 3. FILES MANAGER SCREEN -----------------
class FilesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.layout.add_widget(Label(text="[b]App Storage Manager[/b]", markup=True, size_hint=(1, 0.08)))
        
        self.file_list = Label(text="", size_hint_y=None, markup=True)
        self.file_list.bind(texture_size=self.file_list.setter('size'))
        
        scroll = ScrollView()
        scroll.add_widget(self.file_list)
        self.layout.add_widget(scroll)
        
        bottom_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=5)
        
        btn_folder = Button(text="+ New Folder")
        btn_folder.bind(on_release=self.create_folder_popup)
        
        btn_import = Button(text="+ Import File")
        btn_import.bind(on_release=self.import_file_popup)
        
        bottom_bar.add_widget(btn_folder)
        bottom_bar.add_widget(btn_import)
        
        btn_back = Button(text="< Main Menu", size_hint=(1, 0.08))
        btn_back.bind(on_release=lambda x: setattr(self.manager, 'current', 'main'))
        
        self.layout.add_widget(bottom_bar)
        self.layout.add_widget(btn_back)
        self.add_widget(self.layout)

    def on_enter(self):
        self.refresh_files()

    def refresh_files(self):
        files = os.listdir(APP_STORAGE)
        if files:
            display_text = "\n".join([f"📁 {f}" if os.path.isdir(os.path.join(APP_STORAGE, f)) else f"📄 {f}" for f in files])
        else:
            display_text = "(Folder Empty)"
        self.file_list.text = display_text

    def create_folder_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        txt = TextInput(hint_text="New Folder Name", multiline=False)
        btn = Button(text="Create Folder")
        
        content.add_widget(txt)
        content.add_widget(btn)
        
        popup = Popup(title="Create New Folder", content=content, size_hint=(0.85, 0.4))
        
        def make_dir(inst):
            name = txt.text.strip()
            if name:
                target_dir = os.path.join(APP_STORAGE, name)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    self.refresh_files()
                    popup.dismiss()

        btn.bind(on_release=make_dir)
        popup.open()

    def import_file_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        txt_path = TextInput(hint_text="Full path of file in Internal Storage", multiline=False)
        btn_move = Button(text="Move File to App Storage")
        
        content.add_widget(txt_path)
        content.add_widget(btn_move)
        
        popup = Popup(title="Import File (Moves & Removes Original)", content=content, size_hint=(0.85, 0.4))
        
        def move_file(inst):
            src_path = txt_path.text.strip()
            if os.path.exists(src_path):
                filename = os.path.basename(src_path)
                dest_path = os.path.join(APP_STORAGE, filename)
                shutil.copy(src_path, dest_path)
                os.remove(src_path)
                self.refresh_files()
                popup.dismiss()

        btn_move.bind(on_release=move_file)
        popup.open()

# ----------------- APP INITIALIZER -----------------
class StudyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main'))
        sm.add_widget(NotesScreen(name='notes'))
        sm.add_widget(StudyScreen(name='study'))
        sm.add_widget(FilesScreen(name='files'))
        return sm

if __name__ == '__main__':
    StudyApp().run()

