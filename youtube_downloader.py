import sys
import os
import subprocess
import urllib.request
import platform
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QComboBox, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from pytube import Playlist, YouTube

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_ffmpeg():
    system = platform.system().lower()
    url = ""
    ffmpeg_dir = "ffmpeg"
    if system == "windows":
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        ffmpeg_zip = "ffmpeg.zip"
    elif system == "darwin":
        url = "https://evermeet.cx/ffmpeg/ffmpeg-4.4.1.zip"
        ffmpeg_zip = "ffmpeg.zip"
    elif system == "linux":
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        ffmpeg_zip = "ffmpeg.tar.xz"
    else:
        print("Unsupported OS. Please install ffmpeg manually.")
        return

    urllib.request.urlretrieve(url, ffmpeg_zip)
    if system == "windows":
        import zipfile
        with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        os.remove(ffmpeg_zip)
        os.environ["PATH"] += os.pathsep + os.path.abspath(ffmpeg_dir)
    elif system == "darwin":
        import zipfile
        with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        os.remove(ffmpeg_zip)
        os.environ["PATH"] += os.pathsep + os.path.abspath(ffmpeg_dir)
    elif system == "linux":
        import tarfile
        with tarfile.open(ffmpeg_zip, 'r:xz') as tar_ref:
            tar_ref.extractall(ffmpeg_dir)
        os.remove(ffmpeg_zip)
        os.environ["PATH"] += os.pathsep + os.path.abspath(ffmpeg_dir)

class DownloadThread(QThread):
    log = pyqtSignal(str)

    def __init__(self, url, output_path, is_playlist, download_format, audio_quality, video_quality):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.is_playlist = is_playlist
        self.download_format = download_format
        self.audio_quality = audio_quality
        self.video_quality = video_quality

    def run(self):
        if self.is_playlist:
            self.download_playlist(self.url, self.output_path)
        else:
            self.download_video(self.url, self.output_path)

    def download_video(self, url, output_path):
        try:
            yt = YouTube(url)
            if self.download_format == 'mp4':
                video_streams = yt.streams.filter(progressive=True, file_extension='mp4')
                stream = video_streams.filter(res=self.video_quality).first()
                if not stream:
                    stream = video_streams.order_by('resolution').desc().first()
            else:  # mp3
                audio_streams = yt.streams.filter(only_audio=True)
                if self.audio_quality == 'high (320kbps)':
                    stream = audio_streams.filter(abr='320kbps').first()
                elif self.audio_quality == 'high (192kbps)':
                    stream = audio_streams.filter(abr='192kbps').first()
                elif self.audio_quality == 'medium (160kbps)':
                    stream = audio_streams.filter(abr='160kbps').first()
                elif self.audio_quality == 'medium (128kbps)':
                    stream = audio_streams.filter(abr='128kbps').first()
                else:  # low (64kbps)
                    stream = audio_streams.filter(abr='64kbps').first()

            output_file = stream.download(output_path=output_path)
            if self.download_format == 'mp3':
                base, ext = os.path.splitext(output_file)
                new_file = base + '.mp3'
                subprocess.run(['ffmpeg', '-i', output_file, new_file])
                os.remove(output_file)

            self.log.emit(f"Downloaded: {yt.title}")
        except Exception as e:
            self.log.emit(f"Error: {e}")

    def download_playlist(self, playlist_url, output_path):
        try:
            playlist = Playlist(playlist_url)
            self.log.emit(f"Playlist Title: {playlist.title}")
            self.log.emit(f"Total Videos: {len(playlist.video_urls)}")

            if not os.path.exists(output_path):
                os.makedirs(output_path)

            for url in playlist.video_urls:
                self.download_video(url, output_path)
        except Exception as e:
            self.log.emit(f"Error: {e}")

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('YouTube Downloader')
        self.setGeometry(100, 100, 500, 600)

        layout = QVBoxLayout()

        self.linkLabel = QLabel('Enter YouTube Link (Playlist or Video):')
        layout.addWidget(self.linkLabel)

        self.linkInput = QLineEdit(self)
        layout.addWidget(self.linkInput)

        self.formatLabel = QLabel('Select Download Format:')
        layout.addWidget(self.formatLabel)

        self.formatComboBox = QComboBox(self)
        self.formatComboBox.addItem('mp4')
        self.formatComboBox.addItem('mp3')
        self.formatComboBox.currentIndexChanged.connect(self.update_quality_options)
        layout.addWidget(self.formatComboBox)

        self.qualityLabel = QLabel('Select Audio Quality (for mp3) or Video Quality (for mp4):')
        layout.addWidget(self.qualityLabel)

        self.audioQualityComboBox = QComboBox(self)
        self.audioQualityComboBox.addItem('high (320kbps)')
        self.audioQualityComboBox.addItem('high (192kbps)')
        self.audioQualityComboBox.addItem('medium (160kbps)')
        self.audioQualityComboBox.addItem('medium (128kbps)')
        self.audioQualityComboBox.addItem('low (64kbps)')
        layout.addWidget(self.audioQualityComboBox)

        self.videoQualityComboBox = QComboBox(self)
        self.videoQualityComboBox.addItem('1080p')
        self.videoQualityComboBox.addItem('720p')
        self.videoQualityComboBox.addItem('480p')
        self.videoQualityComboBox.addItem('360p')
        self.videoQualityComboBox.addItem('240p')
        self.videoQualityComboBox.addItem('144p')
        layout.addWidget(self.videoQualityComboBox)

        self.outputPathLabel = QLabel('Select Output Directory:')
        layout.addWidget(self.outputPathLabel)

        self.outputPathButton = QPushButton('Browse', self)
        self.outputPathButton.clicked.connect(self.browse_folder)
        layout.addWidget(self.outputPathButton)

        self.outputPathDisplay = QLabel(self)
        layout.addWidget(self.outputPathDisplay)

        self.downloadButton = QPushButton('Download', self)
        self.downloadButton.clicked.connect(self.download)
        layout.addWidget(self.downloadButton)

        self.logOutput = QTextEdit(self)
        self.logOutput.setReadOnly(True)
        layout.addWidget(self.logOutput)

        self.setLayout(layout)
        self.update_quality_options()

    def update_quality_options(self):
        if self.formatComboBox.currentText() == 'mp3':
            self.audioQualityComboBox.setEnabled(True)
            self.qualityLabel.setEnabled(True)
            self.videoQualityComboBox.setEnabled(False)
        else:
            self.audioQualityComboBox.setEnabled(False)
            self.qualityLabel.setEnabled(True)
            self.videoQualityComboBox.setEnabled(True)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if folder:
            self.outputPathDisplay.setText(folder)

    def log_message(self, message):
        self.logOutput.append(message)

    def download(self):
        url = self.linkInput.text()
        output_path = self.outputPathDisplay.text()
        download_format = self.formatComboBox.currentText()
        audio_quality = self.audioQualityComboBox.currentText()
        video_quality = self.videoQualityComboBox.currentText()

        if not url or not output_path:
            self.log_message('Please provide both a YouTube link and an output directory.')
            return

        is_playlist = 'playlist' in url
        self.thread = DownloadThread(url, output_path, is_playlist, download_format, audio_quality, video_quality)
        self.thread.log.connect(self.log_message)
        self.thread.start()

    def check_ffmpeg_installation(self):
        if not check_ffmpeg():
            reply = QMessageBox.question(self, 'FFmpeg not found', 'FFmpeg is not installed. Would you like to download and install it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                download_ffmpeg()
                QMessageBox.information(self, 'FFmpeg', 'FFmpeg has been installed successfully.')
            else:
                QMessageBox.warning(self, 'FFmpeg', 'FFmpeg is required for this application to function properly.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.check_ffmpeg_installation()
    downloader.show()
    sys.exit(app.exec_())
