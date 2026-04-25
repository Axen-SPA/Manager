import sys
import psutil
import platform
import datetime
import os
import subprocess
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QHeaderView,
    QSplashScreen
)

def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return filename

def bytes_to_human(n):
    symbols = ('B','KB','MB','GB','TB')
    i=0
    while n>=1024 and i<len(symbols)-1:
        n/=1024.
        i+=1
    return f"{n:.1f} {symbols[i]}"

def wmic_query(args):
    try:
        out=subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL)
        return [l.strip() for l in out.split("\n") if l.strip()]
    except:
        return []

def get_gpu_info():
    lines=wmic_query(["wmic","path","win32_VideoController","get","Name,AdapterRAM,DriverVersion"])
    g=[]
    for l in lines[1:]:
        p=l.split()
        if len(p)>=3:
            name=" ".join(p[:-2])
            ram=p[-2]
            drv=p[-1]
            try: ram_h=bytes_to_human(int(ram))
            except: ram_h="不明"
            g.append((name,ram_h,drv))
    return g

def get_disk_info():
    lines=wmic_query(["wmic","diskdrive","get","Model,Size,InterfaceType"])
    d=[]
    for l in lines[1:]:
        p=l.split()
        if len(p)>=3:
            model=" ".join(p[:-2])
            size=p[-2]
            iface=p[-1]
            try: size_h=bytes_to_human(int(size))
            except: size_h="不明"
            d.append((model,size_h,iface))
    return d

def get_nic_info():
    lines=wmic_query(["wmic","nic","get","Name,MACAddress,Speed"])
    n=[]
    for l in lines[1:]:
        p=l.split()
        if len(p)>=3:
            name=" ".join(p[:-2])
            mac=p[-2]
            spd=p[-1]
            n.append((name,mac,spd))
    return n

def get_installed_apps():
    lines=wmic_query(["wmic","product","get","Name,Version"])
    a=[]
    for l in lines[1:]:
        p=l.split()
        if len(p)>=2:
            name=" ".join(p[:-1])
            ver=p[-1]
            a.append((name,ver))
    return a

class GraphWidget(QWidget):
    def __init__(self,title,unit,color,max_value,parent=None):
        super().__init__(parent)
        self.title=title
        self.unit=unit
        self.color=color
        self.max_value=max_value
        self.history=[]
        self.max_points=120
        self.setMinimumHeight(180)
        self.title_label=QLabel(f"{self.title} [{self.unit}]",self)
        self.title_label.setStyleSheet("color:white;")
        self.title_label.setFont(QFont("Consolas",11))

    def add_value(self,v):
        self.history.append(float(v))
        if len(self.history)>self.max_points:
            self.history.pop(0)

    def paintEvent(self,e):
        if not self.history: return
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(),QColor(15,15,15))
        self.title_label.move(8,4)
        left=40; top=25
        w=self.width()-left-10
        h=self.height()-top-10
        p.setPen(QPen(QColor(60,60,60),1))
        for i in range(5):
            y=top+(h*i/4)
            p.drawLine(int(left),int(y),int(left+w),int(y))
        p.setPen(QPen(QColor(200,200,200),1))
        p.drawLine(int(left),int(top),int(left),int(top+h))
        for i in range(5):
            val=self.max_value-(self.max_value*i/4)
            y=top+(h*i/4)
            p.drawText(5,int(y+5),f"{val:.0f}")
        p.setPen(QPen(self.color,2))
        n=len(self.history)
        for i in range(1,n):
            x1=left+(w*(i-1)/(self.max_points-1))
            x2=left+(w*i/(self.max_points-1))
            v1=max(0,min(self.history[i-1],self.max_value))
            v2=max(0,min(self.history[i],self.max_value))
            y1=top+h-(v1/self.max_value)*h
            y2=top+h-(v2/self.max_value)*h
            p.drawLine(int(x1),int(y1),int(x2),int(y2))

class AxenSystemManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AxenSystem Manager")
        self.resize(1400,850)
        self.setStyleSheet("background-color:#101010;color:white;")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        self.tabs=QTabWidget()
        self.setCentralWidget(self.tabs)

        self.monitor_tab=QWidget()
        self.process_tab=QWidget()
        self.hw_tab=QWidget()
        self.sw_tab=QWidget()
        self.apps_tab=QWidget()
        self.about_tab=QWidget()

        self.tabs.addTab(self.monitor_tab,"モニター")
        self.tabs.addTab(self.process_tab,"プロセス")
        self.tabs.addTab(self.hw_tab,"ハードウェア情報")
        self.tabs.addTab(self.sw_tab,"ソフトウェア情報")
        self.tabs.addTab(self.apps_tab,"インストール済みアプリ")
        self.tabs.addTab(self.about_tab,"このアプリについて")

        self.init_monitor_tab()
        self.init_process_tab()
        self.init_hw_tab()
        self.init_sw_tab()
        self.init_apps_tab()
        self.init_about_tab()

        self.last_net=psutil.net_io_counters()
        self.last_time=time.time()
        self.frame_count=0
        self.fps=0.0

        for _ in range(5):
            self.update_monitor_once()

        self.update_processes_once()
        self.load_hw_info()
        self.load_sw_info()
        self.load_apps_once()

        self.monitor_timer=QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor_once)
        self.monitor_timer.start(1000)

        self.render_timer=QTimer()
        self.render_timer.timeout.connect(self.render_frame)
        self.render_timer.start(8)

    def init_about_tab(self):
        l=QVBoxLayout()
        pix=QPixmap(resource_path("about.png"))
        pix=pix.scaled(pix.width()//2,pix.height()//2,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        img=QLabel(); img.setPixmap(pix); img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t=QLabel("AxenSystemManagerはAxenSystemによる軽量高速の Windows 管理ツールです。")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size:15px;color:white;")
        link=QLabel('<a href="https://axen.jp">https://axen.jp</a>')
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setOpenExternalLinks(True)
        link.setStyleSheet("font-size:16px;color:#00FF9C;")
        v=QLabel("AxenSystem Manager v3")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setStyleSheet("font-size:14px;color:#00FF9C;")
        l.addWidget(img); l.addWidget(t); l.addWidget(link); l.addWidget(v)
        self.about_tab.setLayout(l)

    def init_monitor_tab(self):
        l=QVBoxLayout()
        t=QHBoxLayout()
        b=QHBoxLayout()
        self.cpu_graph=GraphWidget("CPU 使用率","%",QColor(0,255,156),100)
        self.mem_graph=GraphWidget("メモリ使用率","%",QColor(0,200,255),100)
        self.disk_graph=GraphWidget("ディスク使用率","%",QColor(255,215,0),100)
        self.net_graph=GraphWidget("ネットワーク受信速度","KB/s",QColor(0,255,156),5000)
        self.fps_label=QLabel("FPS: 0.00")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.fps_label.setStyleSheet("color:#00FF9C;font-family:Consolas;font-size:14px;")
        t.addWidget(self.cpu_graph); t.addWidget(self.mem_graph)
        b.addWidget(self.disk_graph); b.addWidget(self.net_graph)
        l.addLayout(t); l.addLayout(b); l.addWidget(self.fps_label)
        self.monitor_tab.setLayout(l)

    def update_monitor_once(self):
        cpu=psutil.cpu_percent(interval=0.0)
        mem=psutil.virtual_memory().percent
        disk=psutil.disk_usage("/").percent
        now=psutil.net_io_counters()
        down=(now.bytes_recv-self.last_net.bytes_recv)/1024
        self.last_net=now
        self.cpu_graph.add_value(cpu)
        self.mem_graph.add_value(mem)
        self.disk_graph.add_value(disk)
        self.net_graph.add_value(down)

    def render_frame(self):
        self.frame_count+=1
        now=time.time()
        e=now-self.last_time
        if e>=1.0:
            self.fps=self.frame_count/e
            self.frame_count=0
            self.last_time=now
            self.fps_label.setText(f"FPS: {self.fps:.2f}")
        self.cpu_graph.update()
        self.mem_graph.update()
        self.disk_graph.update()
        self.net_graph.update()

    def init_process_tab(self):
        l=QVBoxLayout()
        self.proc_table=QTableWidget()
        self.proc_table.setColumnCount(7)
        self.proc_table.setHorizontalHeaderLabels(["PID","プロセス名","CPU%","メモリ","スレッド数","ハンドル数","実行パス"])
        h=self.proc_table.horizontalHeader()
        for i in range(7): h.setSectionResizeMode(i,QHeaderView.ResizeMode.Stretch)
        l.addWidget(self.proc_table)
        self.process_tab.setLayout(l)

    def update_processes_once(self):
        p_list=[]
        for p in psutil.process_iter(["pid","name","cpu_percent","memory_info","num_threads"]):
            try:
                mem=bytes_to_human(p.info["memory_info"].rss)
                pid=p.info["pid"]
                name=p.info["name"]
                cpu=p.info["cpu_percent"]
                th=p.info["num_threads"]
                try: hd=p.num_handles()
                except: hd="N/A"
                try: ex=p.exe()
                except: ex="不明"
                p_list.append((pid,name,cpu,mem,th,hd,ex))
            except:
                continue
        p_list.sort(key=lambda x:x[2],reverse=True)
        p_list=p_list[:120]
        self.proc_table.setRowCount(len(p_list))
        for r,d in enumerate(p_list):
            for c,v in enumerate(d):
                self.proc_table.setItem(r,c,QTableWidgetItem(str(v)))

    def init_hw_tab(self):
        l=QVBoxLayout()
        self.hw_text=QTextEdit()
        self.hw_text.setReadOnly(True)
        l.addWidget(self.hw_text)
        self.hw_tab.setLayout(l)

    def load_hw_info(self):
        lines=[]
        lines.append("【CPU】")
        lines.append(f"名称: {platform.processor()}")
        lines.append(f"物理コア: {psutil.cpu_count(logical=False)}")
        lines.append(f"論理コア: {psutil.cpu_count(logical=True)}\n")
        vm=psutil.virtual_memory()
        lines.append("【メモリ】")
        lines.append(f"総容量: {bytes_to_human(vm.total)}")
        lines.append(f"使用中: {bytes_to_human(vm.used)}")
        lines.append(f"空き: {bytes_to_human(vm.available)}\n")
        d=get_disk_info()
        lines.append("【ディスク】")
        for x in d:
            lines.append(f"モデル: {x[0]}")
            lines.append(f"容量: {x[1]}")
            lines.append(f"接続: {x[2]}\n")
        g=get_gpu_info()
        lines.append("【GPU】")
        for x in g:
            lines.append(f"名称: {x[0]}")
            lines.append(f"VRAM: {x[1]}")
            lines.append(f"ドライバ: {x[2]}\n")
        n=get_nic_info()
        lines.append("【ネットワーク】")
        for x in n:
            lines.append(f"名称: {x[0]}")
            lines.append(f"MAC: {x[1]}")
            lines.append(f"速度: {x[2]}\n")
        self.hw_text.setPlainText("\n".join(lines))

    def init_sw_tab(self):
        l=QVBoxLayout()
        self.sw_text=QTextEdit()
        self.sw_text.setReadOnly(True)
        l.addWidget(self.sw_text)
        self.sw_tab.setLayout(l)

    def load_sw_info(self):
        lines=[]
        lines.append("【OS】")
        lines.append(f"{platform.system()} {platform.release()}")
        lines.append(f"バージョン: {platform.version()}")
        lines.append(f"ユーザー: {os.getlogin()}\n")
        bt=datetime.datetime.fromtimestamp(psutil.boot_time())
        lines.append("【起動情報】")
        lines.append(f"最終起動: {bt}\n")
        lines.append("【Python】")
        lines.append(f"バージョン: {platform.python_version()}")
        lines.append(f"実行ファイル: {sys.executable}")
        self.sw_text.setPlainText("\n".join(lines))

    def init_apps_tab(self):
        l=QVBoxLayout()
        self.apps_table=QTableWidget()
        self.apps_table.setColumnCount(2)
        self.apps_table.setHorizontalHeaderLabels(["アプリ名","バージョン"])
        h=self.apps_table.horizontalHeader()
        h.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        l.addWidget(self.apps_table)
        self.apps_tab.setLayout(l)

    def load_apps_once(self):
        a=get_installed_apps()
        self.apps_table.setRowCount(len(a))
        for r,(n,v) in enumerate(a):
            self.apps_table.setItem(r,0,QTableWidgetItem(n))
            self.apps_table.setItem(r,1,QTableWidgetItem(v))


if __name__=="__main__":
    app=QApplication(sys.argv)

    original_pix=QPixmap(resource_path("splash.png"))
    scaled_pix=original_pix.scaled(
        original_pix.width()//3,
        original_pix.height()//3,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    splash=QSplashScreen(scaled_pix,Qt.WindowType.WindowStaysOnTopHint)
    splash.setMask(scaled_pix.mask())
    splash.show()

    win=AxenSystemManager()
    splash.finish(win)
    win.show()

    sys.exit(app.exec())
