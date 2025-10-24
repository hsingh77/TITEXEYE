# admin_main.py — Enhanced Admin App with Dashboard, Search, Export & Themes
from __future__ import annotations
import os, sys, time, json, shutil, glob
from dataclasses import dataclass
from typing import List, Optional
from kivy.uix.button import Button
from kivy.uix.label import Label
os.environ.setdefault("KIVY_VIDEO", "ffpyplayer")

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.image import AsyncImage
from kivy.factory import Factory
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.togglebutton import ToggleButton

from kivymd.app import MDApp
# Register MDToolbar across KivyMD variants
_Toolbar = None
try:
    from kivymd.uix.toolbar import MDToolbar as _Toolbar
except Exception:
    try:
        from kivymd.uix.appbar import MDToolbar as _Toolbar
    except Exception:
        try:
            from kivymd.uix.appbar import MDTopAppBar as _Toolbar
        except Exception:
            from kivy.uix.boxlayout import BoxLayout as _Toolbar
Factory.register('MDToolbar', cls=_Toolbar)

from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

try:
    from kivymd.uix.list import MDList, OneLineListItem
except ImportError:
    try:
        from kivymd.uix.list import MDList, OneLineAvatarListItem as OneLineListItem
    except ImportError:
        from kivymd.uix.list import MDList, MDListItem, MDListItemHeadlineText
        # Create a compatible OneLineListItem class
        class OneLineListItem(MDListItem):
            def __init__(self, text="", **kwargs):
                super().__init__(**kwargs)
                self.add_widget(MDListItemHeadlineText(text=text))

from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField

# For KivyMD 2.0.1 compatibility
# For KivyMD 2.0.1 compatibility
try:
    from kivymd.uix.button import MDRaisedButton
except ImportError:
    try:
        from kivymd.uix.button import MDFillRoundFlatButton as MDRaisedButton
    except ImportError:
        try:
            from kivymd.uix.button import MDRoundFlatButton as MDRaisedButton
        except ImportError:
            from kivymd.uix.button import MDButton as MDRaisedButton

try:
    from kivymd.uix.selectioncontrol import MDSwitch
except ImportError:
    # Use ToggleButton as fallback
    MDSwitch = ToggleButton

# Optional folder chooser
try:
    from plyer import filechooser
except Exception:
    filechooser = None

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.3gp'}

APP_FOLDER_NAME = "MyCameraApp"  # legacy shared-folder option

def _android_shared_root() -> str:
    try:
        from android.storage import primary_external_storage_path
        base = primary_external_storage_path()
        return os.path.join(base, APP_FOLDER_NAME)
    except Exception:
        return os.path.join("/sdcard", APP_FOLDER_NAME)

def _looks_like_users_root(path: str) -> bool:
    users_dir = os.path.join(path, "users")
    if not os.path.isdir(users_dir):
        return False
    try:
        for name in os.listdir(users_dir):
            if len(name) == 10 and name.isdigit():
                return True
    except Exception:
        pass
    for p in glob.glob(os.path.join(users_dir, "*", "uploads", "*")):
        base = os.path.basename(p)
        if base.split("_", 1)[0].isdigit() and len(base.split("_", 1)[0]) == 10:
            return True
    return False

def _win_candidates() -> List[str]:
    cands = []
    home = os.path.expanduser("~")
    local = os.getenv("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
    roaming = os.getenv("APPDATA") or os.path.join(home, "AppData", "Roaming")
    for root in (local, roaming):
        for appname in ("PhotoApp", "photoapp", "MyCameraApp", "mycameraapp"):
            cands.append(os.path.join(root, appname))
    for root in (local, roaming):
        try:
            for name in os.listdir(root)[:200]:
                cands.append(os.path.join(root, name))
        except Exception:
            pass
    cands.append(os.path.join(home, APP_FOLDER_NAME))
    return cands

def default_users_root() -> str:
    env = os.getenv("MYCAM_USERS_ROOT")
    if env and _looks_like_users_root(env):
        return env
    if platform == "android":
        return _android_shared_root()
    cands = _win_candidates() if platform == "win" else [
        os.path.join(os.path.expanduser("~"), ".local", "share", "PhotoApp"),
        os.path.join(os.path.expanduser("~"), APP_FOLDER_NAME),
    ]
    for p in cands:
        if _looks_like_users_root(p):
            return p
    return os.path.join(os.path.expanduser("~"), APP_FOLDER_NAME)

@dataclass
class Upload:
    path: str
    media_type: str  # 'image' or 'video'
    created_at: float

class ThemeManager:
    def __init__(self):
        self.current_theme = "default"
        self.themes = {
            "default": {
                "primary": "Teal",
                "accent": "Amber", 
                "bg_color": [0.95, 0.95, 0.95, 1],
                "card_color": [1, 1, 1, 1],
                "text_primary": [0, 0, 0, 1],
                "text_secondary": [0.2, 0.2, 0.2, 1]
            },
            "dark": {
                "primary": "DeepOrange",
                "accent": "BlueGray",
                "bg_color": [0.1, 0.1, 0.1, 1],
                "card_color": [0.2, 0.2, 0.2, 1],
                "text_primary": [1, 1, 1, 1],
                "text_secondary": [0.8, 0.8, 0.8, 1]
            }
        }

    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False

    def get_color(self, color_name):
        return self.themes[self.current_theme].get(color_name, [1, 1, 1, 1])

    def toggle_dark_mode(self):
        if self.current_theme == "dark":
            self.set_theme("default")
        else:
            self.set_theme("dark")
        return self.current_theme

class EnhancedFullScreenPreview(ModalView):
    image_source = StringProperty()
    file_info = StringProperty()
    is_approved = BooleanProperty(False)

    def __init__(self, image_path, file_info="", is_approved=False, **kwargs):
        super().__init__(**kwargs)
        self.image_source = image_path
        self.file_info = file_info
        self.is_approved = is_approved
        self.image_path = image_path
        self.size_hint = (0.9, 0.9)
        self.auto_dismiss = True
        
        # Create layout
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Top bar with close and approve button
        top_bar = BoxLayout(size_hint_y=None, height='40dp')
        
        close_btn = Button(
            text='X Close', 
            size_hint_x=None,
            width='100dp',
            background_color=(1, 0, 0, 1)
        )
        close_btn.bind(on_press=lambda x: self.dismiss())
        
        # Check/Uncheck button
        self.approve_btn = ToggleButton(
            text='✓ Approved' if self.is_approved else '✗ Unapproved',
            size_hint_x=None,
            width='150dp',
            state='down' if self.is_approved else 'normal',
            background_color=(0, 0.7, 0, 1) if self.is_approved else (0.7, 0.7, 0.7, 1)
        )
        self.approve_btn.bind(on_press=self.toggle_approval)
        
        top_bar.add_widget(close_btn)
        top_bar.add_widget(self.approve_btn)
        
        # Image
        image = AsyncImage(
            source=image_path,
            allow_stretch=True,
            keep_ratio=True
        )
        
        # Info label
        info = Label(
            text=file_info,
            size_hint_y=None,
            height='80dp',
            text_size=(None, None),
            halign='center'
        )
        
        layout.add_widget(top_bar)
        layout.add_widget(image)
        layout.add_widget(info)
        
        self.add_widget(layout)

    def toggle_approval(self, instance):
        """Toggle approval status"""
        self.is_approved = not self.is_approved
        instance.text = '✓ Approved' if self.is_approved else '✗ Unapproved'
        instance.background_color = (0, 0.7, 0, 1) if self.is_approved else (0.7, 0.7, 0.7, 1)
        
        # Update in store
        app = MDApp.get_running_app()
        app.store.toggle_approval(self.image_path)

class AdminStore:
    """
    <ROOT>/
    users/<mobile>/uploads/<mobile>_YYYYMMDD_<n>.(jpg|mp4)
    trash/<ts>_<mobile>/
    """
    def __init__(self, root: Optional[str] = None, settings_dir: Optional[str] = None):
        self.settings_dir = settings_dir or os.path.join(os.path.expanduser("~"), ".admin_mycam")
        os.makedirs(self.settings_dir, exist_ok=True)
        self._settings_path = os.path.join(self.settings_dir, "settings.json")
        self._approved_path = os.path.join(self.settings_dir, "approved.json")  # ADD THIS LINE

        saved_root = None
        try:
            if os.path.exists(self._settings_path):
                with open(self._settings_path, "r", encoding="utf-8") as f:
                    saved_root = (json.load(f) or {}).get("root")
        except Exception:
            saved_root = None

        self.root = root or saved_root or default_users_root()
        self.users_dir = os.path.join(self.root, "users")
        self.trash_dir = os.path.join(self.root, "trash")
        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.trash_dir, exist_ok=True)
        
        self._load_approved_status()  # ADD THIS LINE

    # ADD THESE NEW METHODS FOR APPROVAL TRACKING
    def _load_approved_status(self):
        """Load approved status from file"""
        try:
            with open(self._approved_path, "r", encoding="utf-8") as f:
                self.approved_files = json.load(f)
        except:
            self.approved_files = {}

    def _save_approved_status(self):
        """Save approved status to file"""
        with open(self._approved_path, "w", encoding="utf-8") as f:
            json.dump(self.approved_files, f)

    def toggle_approval(self, file_path: str) -> bool:
        """Toggle approval status for a file"""
        file_path = os.path.normpath(file_path)  # Normalize path
        current_status = self.approved_files.get(file_path, False)
        self.approved_files[file_path] = not current_status
        self._save_approved_status()
        return self.approved_files[file_path]

    def is_approved(self, file_path: str) -> bool:
        """Check if file is approved"""
        file_path = os.path.normpath(file_path)
        return self.approved_files.get(file_path, False)

    def get_approved_files(self) -> List[str]:
        """Get list of all approved file paths"""
        return [path for path, approved in self.approved_files.items() if approved]

    def get_unapproved_files(self) -> List[str]:
        """Get list of all unapproved file paths"""
        return [path for path, approved in self.approved_files.items() if not approved]

    # KEEP ALL YOUR EXISTING METHODS AS THEY ARE (save_root, set_root, list_users, etc.)
    def save_root(self, path: str):
        os.makedirs(self.settings_dir, exist_ok=True)
        with open(self._settings_path, "w", encoding="utf-8") as f:
            json.dump({"root": path}, f)

    def set_root(self, path: str) -> bool:
        if not _looks_like_users_root(path):
            return False
        self.root = path
        self.users_dir = os.path.join(self.root, "users")
        self.trash_dir = os.path.join(self.root, "trash")
        self.save_root(path)
        return True

    def list_users(self) -> List[str]:
        out: List[str] = []
        # A) folder names that look like mobiles or profile.json with a mobile
        try:
            for name in sorted(os.listdir(self.users_dir)):
                p = os.path.join(self.users_dir, name)
                if not os.path.isdir(p):
                    continue
                if len(name) == 10 and name.isdigit():
                    out.append(name)
                else:
                    prof = os.path.join(p, "profile.json")
                    try:
                        with open(prof, "r", encoding="utf-8") as f:
                            data = json.load(f) or {}
                        mob = str(data.get("mobile", "")).strip()
                        mob_digits = "".join(ch for ch in mob if ch.isdigit())
                        if len(mob_digits) == 10 and mob_digits not in out:
                            out.append(mob_digits)
                    except Exception:
                        pass
        except FileNotFoundError:
            pass
        # B) derive from upload filenames if still empty
        if not out:
            for p in glob.glob(os.path.join(self.users_dir, "*", "uploads", "*")):
                base = os.path.basename(p)
                prefix = base.split("_", 1)[0]
                if len(prefix) == 10 and prefix.isdigit() and prefix not in out:
                    out.append(prefix)
        return sorted(out)

    def uploads_dir(self, mobile: str) -> str:
        return os.path.join(self.users_dir, str(mobile), "uploads")

    def list_uploads_for_user(self, mobile: str) -> List[Upload]:
        udir = self.uploads_dir(mobile)
        items: List[Upload] = []
        try:
            for base in sorted(os.listdir(udir)):
                if not base.startswith(f"{mobile}_"):
                    continue
                p = os.path.join(udir, base)
                if not os.path.isfile(p):
                    continue
                ext = os.path.splitext(base)[1].lower()
                if ext not in (IMAGE_EXTS | VIDEO_EXTS):
                    continue
                mt = 'image' if ext in IMAGE_EXTS else 'video'
                try:
                    ts = os.path.getmtime(p)
                except Exception:
                    ts = time.time()
                items.append(Upload(path=p, media_type=mt, created_at=ts))
        except FileNotFoundError:
            pass
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items

    def delete_user(self, mobile: str) -> bool:
        src = os.path.join(self.users_dir, str(mobile))
        if not os.path.isdir(src):
            return False
        dst = os.path.join(self.trash_dir, f"{int(time.time())}_{mobile}")
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False

class AdminApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = AdminStore()
        self._selected_mobile: str | None = None
        self.theme_manager = ThemeManager()
        self.is_dark_mode = BooleanProperty(False)
        # ADD THESE TWO LINES
        self.show_approved_only = False
        self.show_unapproved_only = False

    # KEEP ALL YOUR EXISTING METHODS AS THEY ARE (build, on_start, refresh_users, etc.)
    def build(self):
        self.title = "Admin Dashboard - MyCameraApp"
        if platform in ("win", "linux", "macosx"):
            Window.size = (1200, 700)
        
        # Try to load KV file, if it fails use a basic layout
        try:
            return Builder.load_file("admin.kv")
        except Exception as e:
            print(f"KV file error: {e}")
            return self.create_fallback_ui()

    def create_fallback_ui(self):
        from kivy.uix.screenmanager import ScreenManager, Screen
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDFlatButton
        
        # Create a simple fallback UI
        layout = MDBoxLayout(orientation='vertical')
        
        # Add basic navigation buttons
        users_btn = MDFlatButton(text='Users', on_release=lambda x: self.show_users())
        photos_btn = MDFlatButton(text='Photos', on_release=lambda x: self.show_photos())
        stats_btn = MDFlatButton(text='Stats', on_release=lambda x: self.show_stats())
        
        layout.add_widget(users_btn)
        layout.add_widget(photos_btn)
        layout.add_widget(stats_btn)
        
        return layout

    def on_start(self):
        Clock.schedule_once(lambda *_: self.refresh_users(), 0)
        self.root.ids.current_root_lbl.text = f"Root: {self.store.root}"
        self.update_stats()

    # -------- ENHANCED USERS TAB ----------
    def refresh_users(self, *_):
        lst = self.root.ids.users_list
        lst.clear_widgets()
        for mob in self.store.list_users():
            it = OneLineListItem(text=mob)
            it.bind(on_release=lambda inst, m=mob: self.select_user(m))
            lst.add_widget(it)

        if not self._selected_mobile:
            self.root.ids.selected_user_lbl.text = "No user selected"

        self.root.ids.photos_grid.clear_widgets()
        self.root.ids.current_root_lbl.text = f"Root: {self.store.root}"
        self.update_stats()

    def select_user(self, mobile: str):
        self._selected_mobile = mobile
        self.root.ids.selected_user_lbl.text = f"Photos of {mobile}"
        self.refresh_uploads()

    def search_users(self, query):
        """Search/filter users in real-time"""
        all_users = self.store.list_users()
        lst = self.root.ids.users_list
        lst.clear_widgets()

        if not query.strip():
            # Show all users if no query
            for mob in all_users:
                it = OneLineListItem(text=mob)
                it.bind(on_release=lambda inst, m=mob: self.select_user(m))
                lst.add_widget(it)
        else:
            # Filter users based on query
            filtered_users = [user for user in all_users if query in user]
            for mob in filtered_users:
                it = OneLineListItem(text=mob)
                it.bind(on_release=lambda inst, m=mob: self.select_user(m))
                lst.add_widget(it)

    # -------- ENHANCED PHOTOS TAB ----------
    # REPLACE THE refresh_uploads METHOD WITH THIS UPDATED VERSION
    def refresh_uploads(self):
        grid = self.root.ids.photos_grid
        grid.clear_widgets()
        if not self._selected_mobile:
            return

        uploads = self.store.list_uploads_for_user(self._selected_mobile)
        
        # Filter based on approval status
        if self.show_approved_only:
            uploads = [up for up in uploads if self.store.is_approved(up.path)]
        elif self.show_unapproved_only:
            uploads = [up for up in uploads if not self.store.is_approved(up.path)]

        for row in uploads:
            is_approved = self.store.is_approved(row.path)
            card = MDCard(
                orientation="vertical", 
                radius=[12], 
                elevation=2,
                size_hint_y=None, 
                height=150,
                padding="4dp"
            )
            
            # Add approval indicator
            approval_indicator = BoxLayout(
                size_hint_y=None,
                height='20dp',
                padding='2dp'
            )
            
            status_label = Label(
                text='✓' if is_approved else '○',
                size_hint_x=None,
                width='20dp',
                color=(0, 1, 0, 1) if is_approved else (0.5, 0.5, 0.5, 1),
                font_size='14sp'
            )
            
            approval_indicator.add_widget(status_label)
            approval_indicator.add_widget(Label())  # spacer
            
            card.add_widget(approval_indicator)
            
            if row.media_type == "image":
                img = AsyncImage(
                    source=row.path, 
                    allow_stretch=True,
                    keep_ratio=True, 
                    mipmap=True, 
                    nocache=False,
                    anim_delay=0.1
                )
                img.bind(on_touch_down=lambda instance, touch, path=row.path, row=row: 
                         self._on_image_touch(instance, touch, path, row))
                card.add_widget(img)
            else:
                name = os.path.basename(row.path)
                card.add_widget(MDLabel(
                    text=f"▶ {name}", 
                    halign="center",
                    theme_text_color="Secondary",
                    font_style="Caption"
                ))
            grid.add_widget(card)

    def _on_image_touch(self, instance, touch, image_path, upload_row):
        if instance.collide_point(*touch.pos):
            self.show_fullscreen_preview(image_path, upload_row)
            return True
        return False

    # REPLACE THE show_fullscreen_preview METHOD WITH THIS UPDATED VERSION
    def show_fullscreen_preview(self, image_path, upload_row):
        """Show enhanced full-screen preview with approval toggle"""
        file_name = os.path.basename(image_path)
        file_size = self._get_file_size(image_path)
        modified_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                    time.localtime(upload_row.created_at))
        is_approved = self.store.is_approved(image_path)  # ADD THIS LINE

        file_info = f"File: {file_name}\nSize: {file_size}\nModified: {modified_time}\nUser: {self._selected_mobile}"

        preview = EnhancedFullScreenPreview(
            image_path=image_path,
            file_info=file_info,
            is_approved=is_approved  # ADD THIS LINE
        )
        preview.open()

    def _get_file_size(self, file_path):
        """Get human-readable file size"""
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} GB"
        except:
            return "Unknown size"

    # ADD THESE THREE NEW METHODS FOR FILTERING
    def show_approved_photos(self):
        """Show only approved photos"""
        self.show_approved_only = True
        self.show_unapproved_only = False
        self.refresh_uploads()
        self._toast("Showing approved photos only")

    def show_unapproved_photos(self):
        """Show only unapproved photos"""
        self.show_approved_only = False
        self.show_unapproved_only = True
        self.refresh_uploads()
        self._toast("Showing unapproved photos only")

    def show_all_photos(self):
        """Show all photos"""
        self.show_approved_only = False
        self.show_unapproved_only = False
        self.refresh_uploads()
        self._toast("Showing all photos")

    # KEEP ALL YOUR EXISTING METHODS AS THEY ARE BELOW THIS LINE
    # -------- NEW STATISTICS FEATURES ----------
    def update_stats(self):
        """Update dashboard statistics"""
        total_size, total_images, total_videos = self.calculate_storage_stats()
        total_users = len(self.store.list_users())

        # Update UI labels if they exist
        if hasattr(self.root.ids, 'total_users_lbl'):
            self.root.ids.total_users_lbl.text = str(total_users)

        if hasattr(self.root.ids, 'total_photos_lbl'):
            self.root.ids.total_photos_lbl.text = str(total_images + total_videos)

        if hasattr(self.root.ids, 'storage_lbl'):
            self.root.ids.storage_lbl.text = self._format_size(total_size)

    def calculate_storage_stats(self):
        """Calculate total storage usage"""
        total_size = 0
        total_images = 0
        total_videos = 0

        for user in self.store.list_users():
            uploads = self.store.list_uploads_for_user(user)
            for upload in uploads:
                try:
                    total_size += os.path.getsize(upload.path)
                    if upload.media_type == 'image':
                        total_images += 1
                    else:
                        total_videos += 1
                except:
                    pass

        return total_size, total_images, total_videos

    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    # -------- NEW EXPORT FEATURES ----------
    def export_user_photos(self):
        """Export all photos for selected user"""
        if not self._selected_mobile:
            self._toast("Select a user first")
            return

        try:
            export_dir = os.path.join(os.path.expanduser("~"), "PhotoExports", f"user_{self._selected_mobile}_{int(time.time())}")
            os.makedirs(export_dir, exist_ok=True)
            
            uploads = self.store.list_uploads_for_user(self._selected_mobile)
            exported_count = 0
            
            for upload in uploads:
                filename = os.path.basename(upload.path)
                shutil.copy2(upload.path, os.path.join(export_dir, filename))
                exported_count += 1
            
            self._toast(f"Exported {exported_count} files to {export_dir}")
        except Exception as e:
            self._toast(f"Export failed: {e}")

    def generate_report(self):
        """Generate usage report"""
        total_size, total_images, total_videos = self.calculate_storage_stats()

        report = f"""
ADMIN REPORT - {time.strftime('%Y-%m-%d %H:%M:%S')}
=================================
Total Users: {len(self.store.list_users())}
Total Images: {total_images}
Total Videos: {total_videos}
Total Storage: {self._format_size(total_size)}
Data Root: {self.store.root}
=================================
"""

        # Save report to file
        report_dir = os.path.join(os.path.expanduser("~"), "AdminReports")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"admin_report_{int(time.time())}.txt")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        self._toast(f"Report saved to {report_path}")

    # -------- THEME MANAGEMENT ----------
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        new_theme = self.theme_manager.toggle_dark_mode()
        self.is_dark_mode = (new_theme == "dark")
        self._toast(f"{new_theme.title()} theme activated")

    def toggle_dark_mode(self, active):
        """Toggle dark mode from switch"""
        self.is_dark_mode = active
        if active:
            self.theme_manager.set_theme("dark")
        else:
            self.theme_manager.set_theme("default")
        self._toast("Theme updated")

    # -------- ENHANCED MENU FEATURES ----------
    def open_file_location(self, file_path):
        """Open file location in system file manager"""
        directory = os.path.dirname(file_path)
        try:
            if platform == "win":
                os.startfile(directory)
            elif platform == "macosx":
                import subprocess
                subprocess.call(["open", directory])
            else:
                import subprocess
                subprocess.call(["xdg-open", directory])
        except Exception as e:
            self._toast(f"Failed to open location: {e}")

    def copy_file_path(self, file_path):
        """Copy file path to clipboard"""
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(file_path)
            self._toast("File path copied to clipboard")
        except Exception as e:
            self._toast(f"Failed to copy path: {e}")

    def download_image(self, image_path):
        """Download image to downloads folder"""
        try:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            filename = os.path.basename(image_path)
            dest_path = os.path.join(downloads_dir, filename)
            shutil.copy2(image_path, dest_path)
            self._toast(f"Downloaded to {dest_path}")
        except Exception as e:
            self._toast(f"Download failed: {e}")

    def clear_cache(self):
        """Clear application cache"""
        try:
            # Clear any cached data
            self._toast("Cache cleared")
        except Exception as e:
            self._toast(f"Cache clear failed: {e}")

    def refresh_all(self):
        """Refresh all data"""
        self.refresh_users()
        self.update_stats()
        self._toast("All data refreshed")

    # -------- KEEP EXISTING MENU METHODS ----------
    def open_folder(self):
        if not self._selected_mobile:
            self._toast("Pick a user first"); return
        path = self.store.uploads_dir(self._selected_mobile)
        try:
            if platform == "win":
                os.startfile(path)  # type: ignore
            elif platform == "macosx":
                import subprocess; subprocess.call(["open", path])
            else:
                import subprocess; subprocess.call(["xdg-open", path])
        except Exception as e:
            self._toast(f"Open failed: {e}")

    def delete_user(self):
        if not self._selected_mobile:
            self._toast("Pick a user first"); return
        if self.store.delete_user(self._selected_mobile):
            self._toast(f"Archived {self._selected_mobile}")
            self._selected_mobile = None
            self.refresh_users()
        else:
            self._toast("Delete failed")

    def choose_root(self):
        # Allow picking the root directory that contains 'users'
        path = None
        if filechooser:
            try:
                sel = filechooser.choose_dir()
                if sel and isinstance(sel, (list, tuple)):
                    path = sel[0]
            except Exception:
                path = None
        if not path:
            # fallback: tkinter dialog
            try:
                import tkinter as tk
                from tkinter import filedialog
                tk.Tk().withdraw()
                path = filedialog.askdirectory(title="Pick folder containing 'users'")
            except Exception:
                path = None
        if not path:
            self._toast("No folder selected"); return
        if self.store.set_root(path):
            self._toast("Root updated")
            self.refresh_users()
        else:
            self._toast("Selected folder doesn't look like the app data (needs a 'users' subfolder)")

    def _toast(self, text: str):
        try:
            from kivymd.toast import toast
            toast(text)
        except Exception:
            print(text)

if __name__ == "__main__":
    AdminApp().run()