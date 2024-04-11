import tempfile
import os

import sublime
import sublime_plugin


class PdfViewerCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        window = self.view.window()
        self.settings = sublime.load_settings('PdfViewer.sublime-settings')

        file_path = self.view.file_name()
        file_extension = os.path.splitext(file_path)[1]

        if file_extension != ".pdf":
            return "File is not a pdf"

        image_path = self.convert_file(file_path)

        if self.settings.get('image_viewer_behavior', 'preview') == "replace_tab":
            self.view.close()
        if self.settings.get('image_viewer_behavior', 'preview') == "preview":
            flag = sublime.TRANSIENT
        else:
            flag = 0

        window.open_file(image_path, flags=flag)


    def convert_file(self, file_path):
        from .packages import fitz
        from .packages.PIL import Image

        file_name = os.path.splitext(os.path.basename(file_path))[0]
        temp_dir = self.get_temp_dir()

        # Create individual images
        doc = fitz.open(file_path)
        for page_nbr, page in enumerate(doc):
            image_path = os.path.join(temp_dir, file_name + f"_{page_nbr}.png")
            pix = page.get_pixmap(dpi=self.settings.get('image_dpi', 100))
            pix.save(image_path)

        doc.close()

        # Concatenate all images
        with Image.open(image_path) as img:
            width, height = img.width, img.height

        final_image = Image.new('RGB', (width, height * (page_nbr + 1)))

        for i in range(page_nbr + 1):
            with Image.open(os.path.join(temp_dir, file_name + f"_{i}.png")) as img:
                final_image.paste(img, (0, height * i))

        final_image_path = os.path.join(temp_dir, file_name + ".png")
        final_image.save(final_image_path)

        return final_image_path


    def get_temp_dir(self):
        temp_dir = os.path.join(tempfile.gettempdir(), "sublime_PdfViewer")

        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        else:
            files = os.listdir(temp_dir)
            for f in files:
                os.remove(os.path.join(temp_dir, f))

        return temp_dir
