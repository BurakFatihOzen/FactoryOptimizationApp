import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import networkx as nx  # Graf çizimi için gerekli
import ctypes
import random
import os
import sys

# Kütüphane kontrolü: Eğer networkx yüklü değilse kullanıcıyı uyarıyoruz
try:
    import networkx as nx
except ImportError:
    print("HATA: 'networkx' kütüphanesi eksik. Lütfen 'pip install networkx' komutunu çalıştırın.")
    sys.exit()

# --- C++ KÜTÜPHANE BAĞLANTISI ---
# Windows (.dll) ve Mac (.dylib) uyumluluğu için dosya uzantılarını kontrol ediyoruz
lib_extensions = ('.dll', '.dylib', '.so')
dll_files = [f for f in os.listdir('.') if f.endswith(lib_extensions) and 'optimization' in f]

if not dll_files:
    print("HATA: C++ kütüphanesi bulunamadı! Lütfen kodu derleyip dosyayı buraya atın.")
    sys.exit()

lib_name = dll_files[0]
try:
    # C++ kodunu Python içerisine yüklüyoruz
    cpp_lib = ctypes.CDLL(f"./{lib_name}")
except Exception as e:
    print(f"HATA: Kütüphane yüklenemedi. Detay: {e}")
    sys.exit()

# C++ tarafındaki Struct yapısının Python karşılığı
# Veri tiplerinin birebir uyuşması gerekiyor (long long -> c_longlong)
class AnalizSonuclari(ctypes.Structure):
    _fields_ = [
        ("sureMs", ctypes.c_longlong),
        ("karsilastirma", ctypes.c_longlong),
        ("swapSayisi", ctypes.c_longlong),
        ("ayarDegisimi", ctypes.c_longlong),
        ("toplamMaliyet", ctypes.c_longlong),
    ]

# C++ fonksiyonlarının parametre tiplerini (argtypes) tanımlıyoruz
# Bu sayede Python verileri C++ pointerlarına doğru çevirebilir
try:
    # Sorting Fonksiyonu
    cpp_lib.sirala_ve_analiz_et.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), 
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(AnalizSonuclari) 
    ]
    # Knapsack Fonksiyonu
    cpp_lib.optimize_uretim_plani.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    ]
    # Dijkstra Fonksiyonu
    cpp_lib.en_kisa_yol_bul.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    ]
    cpp_lib.en_kisa_yol_bul.restype = ctypes.c_int
    
    # Search Fonksiyonu
    cpp_lib.parca_ara.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int]
    cpp_lib.parca_ara.restype = ctypes.c_int

except AttributeError:
    print("HATA: Beklenen fonksiyonlar DLL içinde bulunamadı.")
    sys.exit()

# --- ARAYÜZ (GUI) TASARIMI ---
ctk.set_appearance_mode("Dark") # Modern görünüm için koyu tema
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Fabrika Yönetim & Algoritma Simülasyonu")
        self.geometry("1200x800")
        
        # Sekmeli yapı (Tabview) oluşturuyoruz
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # 3 ana modül için sekmeler
        self.tab_sort = self.tabview.add("1. Üretim Hattı (Sorting)")
        self.tab_plan = self.tabview.add("2. Planlama (Knapsack)")
        self.tab_logi = self.tabview.add("3. Lojistik (Dijkstra/Search)")

        # Sekme içeriklerini kuran fonksiyonları çağır
        self.setup_sorting_tab()
        self.setup_knapsack_tab()
        self.setup_logistics_tab()
        
        self.sorted_data = [] # Arama işlemi için sıralı veriyi burada tutacağız

    # ==========================================
    # SEKME 1: SORTING (SIRALAMA) ARAYÜZÜ
    # ==========================================
    def setup_sorting_tab(self):
        self.tab_sort.grid_columnconfigure(1, weight=1)
        self.tab_sort.grid_rowconfigure(0, weight=1)

        # Sol Menü (Sidebar)
        sidebar = ctk.CTkFrame(self.tab_sort, width=250, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(sidebar, text="HAT OPTİMİZASYONU", font=("Montserrat", 18, "bold")).pack(pady=20)
        
        # Kullanıcı girdileri
        ctk.CTkLabel(sidebar, text="Parça Sayısı:", anchor="w").pack(padx=20, pady=(10,0), anchor="w")
        self.entry_n = ctk.CTkEntry(sidebar)
        self.entry_n.insert(0, "1000") # Varsayılan değer
        self.entry_n.pack(padx=20, pady=5)

        ctk.CTkLabel(sidebar, text="Algoritma:", anchor="w").pack(padx=20, pady=(10,0), anchor="w")
        self.algo_list = ["Insertion Sort", "Shell Sort", "Quick Sort", "Merge Sort", "Heap Sort"]
        self.combo_algo = ctk.CTkComboBox(sidebar, values=self.algo_list)
        self.combo_algo.set("Quick Sort") # Varsayılan hızlı algoritma
        self.combo_algo.pack(padx=20, pady=5)

        self.switch_order = ctk.CTkSwitch(sidebar, text="Azalan Sırada")
        self.switch_order.pack(padx=20, pady=15, anchor="w")

        ctk.CTkButton(sidebar, text="HATTI ÇALIŞTIR", height=40, fg_color="#E04F5F", hover_color="#B0303E", command=self.run_sorting).pack(padx=20, pady=30, fill="x")

        # Sağ Alan (Sonuçlar ve Grafik)
        main_area = ctk.CTkFrame(self.tab_sort, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_sort_res = ctk.CTkLabel(main_area, text="Analiz bekleniyor...", font=("Roboto", 16))
        self.lbl_sort_res.pack(pady=10)

        self.frame_chart_sort = ctk.CTkFrame(main_area, fg_color="#2b2b2b")
        self.frame_chart_sort.pack(fill="both", expand=True)

    def run_sorting(self):
        try: n = int(self.entry_n.get())
        except: return
        
        # Simülasyon için rastgele veri üretiyoruz
        raw_len = [random.randint(1, 1000) for _ in range(n)]
        raw_w = [random.randint(1, 500) for _ in range(n)]
        
        # Python listesini C arrayine dönüştürme
        arr_len = (ctypes.c_int * n)(*raw_len)
        arr_w = (ctypes.c_int * n)(*raw_w)
        
        selected = self.combo_algo.get()
        algo_id = self.algo_list.index(selected) if selected in self.algo_list else 1
        
        res = AnalizSonuclari()
        # C++ fonksiyonunu çağırıyoruz
        cpp_lib.sirala_ve_analiz_et(arr_len, arr_w, n, algo_id, ctypes.byref(res))

        # Sıralanmış veriyi geri alıp saklıyoruz
        self.sorted_data = list(arr_len)
        if self.switch_order.get() == 1:
            self.sorted_data.reverse()
        
        self.lbl_sort_res.configure(text=f"Algoritma: {selected} | Süre: {res.sureMs} ms | Maliyet: {res.toplamMaliyet} TL | Değişim: {res.ayarDegisimi}")
        
        # Sonucu görselleştir
        self.plot_sorting_graph(self.sorted_data)

    def plot_sorting_graph(self, data):
        # Önceki grafiği temizle
        plt.close('all')
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(5,3), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2b2b2b')
        
        # Çok fazla veri varsa sadece ilk 100'ünü gösteriyoruz ki grafik karışmasın
        limit = min(len(data), 100)
        ax.bar(range(limit), data[:limit], color='#4B8BBE', width=0.8)
        ax.set_title(f"Sıralanmış İlk {limit} Ürün")
        ax.grid(alpha=0.2)
        
        # Matplotlib grafiğini Tkinter içine gömme işlemi
        for widget in self.frame_chart_sort.winfo_children(): widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_chart_sort)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ==========================================
    # SEKME 2: KNAPSACK (PLANLAMA) ARAYÜZÜ
    # ==========================================
    def setup_knapsack_tab(self):
        self.tab_plan.grid_columnconfigure(0, weight=1)
        self.tab_plan.grid_columnconfigure(1, weight=1)

        # Sol Panel (Veri Girişi)
        left_frame = ctk.CTkFrame(self.tab_plan)
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(left_frame, text="İŞ LİSTESİ OLUŞTURUCU", font=("Montserrat", 16, "bold")).pack(pady=10)

        # Rastgele iş üretme butonu
        rnd_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        rnd_frame.pack(fill="x", padx=10)
        
        ctk.CTkLabel(rnd_frame, text="İş Sayısı:").pack(side="left", padx=5)
        self.entry_job_n = ctk.CTkEntry(rnd_frame, width=60)
        self.entry_job_n.insert(0, "10")
        self.entry_job_n.pack(side="left", padx=5)
        
        ctk.CTkButton(rnd_frame, text="🎲 Rastgele Doldur", width=120, fg_color="#E59400", hover_color="#B27300", command=self.generate_random_jobs).pack(side="left", padx=5)

        ctk.CTkLabel(left_frame, text="İş Listesi (Süre, Kazanç):", anchor="w").pack(padx=10, pady=(10,0), anchor="w")
        self.txt_jobs = ctk.CTkTextbox(left_frame, height=250)
        self.txt_jobs.insert("0.0", "3, 25\n2, 20\n1, 15\n4, 40\n5, 50")
        self.txt_jobs.pack(padx=10, pady=5, fill="both", expand=True)

        # Kapasite ayarı
        cap_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        cap_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(cap_frame, text="Mesai Kapasitesi (Saat):").pack(side="left", padx=5)
        self.entry_cap = ctk.CTkEntry(cap_frame, width=60)
        self.entry_cap.insert(0, "10")
        self.entry_cap.pack(side="left", padx=5)
        
        ctk.CTkButton(left_frame, text="PLANLARI HESAPLA", height=40, font=("Arial", 14, "bold"), fg_color="#1f6aa5", command=self.run_knapsack).pack(pady=10, fill="x", padx=10)

        # Sağ Panel (Sonuç Gösterimi)
        self.right_frame_plan = ctk.CTkFrame(self.tab_plan)
        self.right_frame_plan.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(self.right_frame_plan, text="ANALİZ SONUCU", font=("Montserrat", 16, "bold")).pack(pady=20)
        self.lbl_knap_res = ctk.CTkLabel(self.right_frame_plan, text="Veri bekleniyor...", font=("Roboto", 16))
        self.lbl_knap_res.pack(pady=20)

    def generate_random_jobs(self):
        try: n = int(self.entry_job_n.get())
        except ValueError: return
        
        self.txt_jobs.delete("0.0", "end")
        for _ in range(n):
            sure = random.randint(1, 10)
            kazanc = random.randint(10, 200)
            self.txt_jobs.insert("end", f"{sure}, {kazanc}\n")

    def run_knapsack(self):
        # Textbox'tan verileri okuyup parse ediyoruz
        text = self.txt_jobs.get("0.0", "end").strip().split('\n')
        times, profits = [], []
        for line in text:
            parts = line.split(',')
            if len(parts) == 2:
                try:
                    times.append(int(parts[0].strip()))
                    profits.append(int(parts[1].strip()))
                except: continue
        
        if not times: return
        
        n = len(times)
        try: cap = int(self.entry_cap.get())
        except: return
        
        arr_t = (ctypes.c_int * n)(*times)
        arr_p = (ctypes.c_int * n)(*profits)
        res_greedy = ctypes.c_int(0)
        res_dp = ctypes.c_int(0)

        # C++ tarafındaki hem Greedy hem DP fonksiyonlarını çalıştır
        cpp_lib.optimize_uretim_plani(arr_t, arr_p, n, cap, ctypes.byref(res_greedy), ctypes.byref(res_dp))

        msg = f"GREEDY (Açgözlü) Kazanç: {res_greedy.value} TL\n(Hızlı ama her zaman en iyi değil)\n\n"
        msg += f"DYNAMIC PROG. Kazanç: {res_dp.value} TL\n(Kesinlikle en iyi sonuç)"
        self.lbl_knap_res.configure(text=msg)

    # ==========================================
    # SEKME 3: LOJİSTİK & ARAMA ARAYÜZÜ
    # ==========================================
    def setup_logistics_tab(self):
        self.tab_logi.grid_columnconfigure(0, weight=1)
        self.tab_logi.grid_columnconfigure(1, weight=2)

        # Sol Panel: Arama (Binary Search)
        frm_search = ctk.CTkFrame(self.tab_logi)
        frm_search.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(frm_search, text="STOK ARAMA", font=("Arial", 14, "bold")).pack(pady=10)
        ctk.CTkLabel(frm_search, text="Aranan Uzunluk (mm):").pack()
        self.entry_search = ctk.CTkEntry(frm_search)
        self.entry_search.pack(pady=5)
        
        ctk.CTkButton(frm_search, text="BUL (Binary Search)", command=self.run_search).pack(pady=10)
        self.lbl_search_res = ctk.CTkLabel(frm_search, text="Durum: Bekleniyor", text_color="gray")
        self.lbl_search_res.pack(pady=10)
        ctk.CTkLabel(frm_search, text="*Önce 1. Sekmede sıralama yapın!", font=("Arial", 10), text_color="gray").pack(side="bottom", pady=10)

        # Sağ Panel: Harita (Dijkstra)
        frm_map = ctk.CTkFrame(self.tab_logi)
        frm_map.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctrl = ctk.CTkFrame(frm_map, height=50)
        ctrl.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ctrl, text="Başlangıç:").pack(side="left", padx=5)
        self.combo_start = ctk.CTkComboBox(ctrl, values=["Depo", "Kesim", "Montaj", "Boya", "Paketleme", "Yükleme"])
        self.combo_start.set("Depo")
        self.combo_start.pack(side="left", padx=5)

        ctk.CTkLabel(ctrl, text="Hedef:").pack(side="left", padx=5)
        self.combo_end = ctk.CTkComboBox(ctrl, values=["Depo", "Kesim", "Montaj", "Boya", "Paketleme", "Yükleme"])
        self.combo_end.set("Yükleme")
        self.combo_end.pack(side="left", padx=5)

        ctk.CTkButton(ctrl, text="ROTA ÇİZ", fg_color="green", command=self.run_dijkstra).pack(side="left", padx=20)

        self.map_frame = ctk.CTkFrame(frm_map)
        self.map_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.draw_dijkstra_map([]) # Başlangıçta boş harita çiz

    def run_search(self):
        # Eğer henüz sıralama yapılmadıysa arama çalışmaz (Binary Search şartı)
        if not self.sorted_data:
            self.lbl_search_res.configure(text="HATA: Önce sıralama yapın!", text_color="red")
            return
        
        try: target = int(self.entry_search.get())
        except: return
        
        n = len(self.sorted_data)
        arr = (ctypes.c_int * n)(*self.sorted_data)
        
        idx = cpp_lib.parca_ara(arr, n, target)
        
        if idx != -1:
            self.lbl_search_res.configure(text=f"BULUNDU!\nIndex: {idx}\n(Depo Rafı #{idx})", text_color="#4B8BBE", font=("Arial", 16, "bold"))
        else:
            self.lbl_search_res.configure(text="STOKTA YOK.", text_color="red", font=("Arial", 16, "bold"))

    def run_dijkstra(self):
        nodes = ["Depo", "Kesim", "Montaj", "Boya", "Paketleme", "Yükleme"]
        s = nodes.index(self.combo_start.get())
        e = nodes.index(self.combo_end.get())

        path_arr = (ctypes.c_int * 10)()
        path_len = ctypes.c_int(0)
        
        # C++ Dijkstra algoritmasını çağırıyoruz
        dist = cpp_lib.en_kisa_yol_bul(s, e, path_arr, ctypes.byref(path_len))
        
        if dist == -1 or dist > 1000:
            print("Yol yok")
            return

        final_path = []
        for i in range(path_len.value):
            final_path.append(path_arr[i])
            
        self.draw_dijkstra_map(final_path, dist)

    def draw_dijkstra_map(self, path, dist=0):
        plt.close('all')
        G = nx.Graph()
        # Graf düğümleri ve mesafeleri (Fabrika planı)
        edges = [(0,1,4), (1,2,8), (2,3,7), (2,5,4), (3,4,9), (3,5,14), (4,5,10)]
        pos = {0:(0,1), 1:(1,1), 2:(2,1), 3:(2,0), 4:(3,0), 5:(3,1)}
        labels = {0:"Depo", 1:"Kesim", 2:"Montaj", 3:"Boya", 4:"Paket", 5:"Yükleme"}

        for u,v,w in edges: G.add_edge(u, v, weight=w)

        fig = plt.figure(figsize=(5,4), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2b2b2b')

        # Düğümleri çiz
        nx.draw(G, pos, ax=ax, with_labels=True, labels=labels, node_color='gray', node_size=1500, font_size=9)
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

        # Eğer rota varsa yeşil ile boya
        if path:
            path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
            nx.draw_networkx_nodes(G, pos, nodelist=path, node_color='#4CAF50', node_size=2000, ax=ax)
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='#4CAF50', width=4, ax=ax)
            ax.set_title(f"Rota Uzunluğu: {dist} metre", color="white", fontsize=12)
        else:
            ax.set_title("Fabrika Yerleşim Planı", color="white")

        for w in self.map_frame.winfo_children(): w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.map_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()