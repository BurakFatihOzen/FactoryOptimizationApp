#include <vector>
#include <algorithm>
#include <chrono>
#include <queue>   // Dijkstra algoritması için
#include <map>     // Graf yapısı için
#include <climits> // Sonsuz (INT_MAX) değeri için

// Windows ve Mac/Linux uyumluluğu için export ayarı
#ifdef _WIN32
    #define DLLEXPORT __declspec(dllexport)
#else
    #define DLLEXPORT
#endif

using namespace std;
using namespace chrono;

// --- VERİ YAPILARI ---

// Üretim hattındaki parçayı temsil eder
struct Parca {
    int id;      // Arama (Search) işlemi için kimlik
    int uzunluk;
    int agirlik;
    int sinif;   // Setup süresini etkileyen parça sınıfı (0-4 arası)
};

// Knapsack problemi için iş yapısı
struct Is {
    int id;
    int sure;    // İşin süresi (maliyet)
    int kazanc;  // İşin getirisi (değer)
};

// --- YARDIMCI FONKSİYONLAR ---

// Parçanın uzunluk ve ağırlığına göre üretim süresini hesaplar
int uretimSuresi(const Parca& p) {
    return (p.uzunluk * 6 + p.agirlik * 4) / 10; // Ağırlıklı ortalama formülü
}

// Makine bir sınıftan diğerine geçerken oluşan ayar (setup) maliyeti
int ayarDegisimMaliyeti(int oncekiSinif, int simdikiSinif) {
    if (oncekiSinif == -1) return 0; // İlk parça için maliyet yok
    // Eğer sınıf değişirse ceza puanı (120) ekle, aynıysa ekleme
    return (oncekiSinif == simdikiSinif) ? 0 : 120;
}

// Sıralama yaparken kullanacağımız karşılaştırma kuralı
// Önce uzunluğa bak, eşitse ağırlığa bak
bool karsilastir(const Parca& a, const Parca& b) {
    if (a.uzunluk != b.uzunluk) return a.uzunluk < b.uzunluk;
    return a.agirlik < b.agirlik;
}

// =======================================================
// BÖLÜM 1: SIRALAMA ALGORİTMALARI (SORTING)
// Amaç: Setup sürelerini minimize etmek için parçaları gruplamak
// =======================================================

// 1. Insertion Sort: Küçük veri setlerinde hızlı ama 10.000 parçada yavaş kalıyor (O(n^2))
void insertionSort(vector<Parca>& dizi, long long& k, long long& s) {
    for (size_t i = 1; i < dizi.size(); i++) {
        Parca key = dizi[i];
        int j = i - 1;
        while (j >= 0) {
            k++; // Karşılaştırma sayacı
            if (karsilastir(key, dizi[j])) {
                dizi[j + 1] = dizi[j];
                s++; // Yer değiştirme (swap) sayacı
                j--;
            } else break;
        }
        dizi[j + 1] = key;
    }
}

// 2. Shell Sort: Insertion Sort'un geliştirilmiş hali, aralıklı sıralama yapar
void shellSort(vector<Parca>& dizi, long long& k, long long& s) {
    int n = dizi.size();
    for (int gap = n / 2; gap > 0; gap /= 2) {
        for (int i = gap; i < n; i++) {
            Parca temp = dizi[i];
            int j = i;
            while (j >= gap) {
                k++;
                if (karsilastir(temp, dizi[j - gap])) {
                    dizi[j] = dizi[j - gap];
                    s++;
                    j -= gap;
                } else break;
            }
            dizi[j] = temp;
        }
    }
}

// 3. Quick Sort: Böl ve Yönet mantığı. Büyük verilerde en performanslısı (O(n log n))
int partitionQS(vector<Parca>& dizi, int low, int high, long long& k, long long& s) {
    Parca pivot = dizi[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        k++;
        if (karsilastir(dizi[j], pivot)) {
            i++;
            swap(dizi[i], dizi[j]);
            s++;
        }
    }
    swap(dizi[i + 1], dizi[high]);
    s++;
    return i + 1;
}

void quickSort(vector<Parca>& dizi, int low, int high, long long& k, long long& s) {
    if (low < high) {
        int pi = partitionQS(dizi, low, high, k, s);
        quickSort(dizi, low, pi - 1, k, s);
        quickSort(dizi, pi + 1, high, k, s);
    }
}

// 4. Merge Sort: Kararlı (stable) sıralama sağlar, bellek kullanımı biraz fazladır
void merge(vector<Parca>& dizi, int l, int m, int r, long long& k, long long& s) {
    vector<Parca> L(dizi.begin() + l, dizi.begin() + m + 1);
    vector<Parca> R(dizi.begin() + m + 1, dizi.begin() + r + 1);
    int i = 0, j = 0, idx = l;
    while (i < (int)L.size() && j < (int)R.size()) {
        k++;
        if (karsilastir(L[i], R[j])) {
            dizi[idx++] = L[i++];
        } else {
            dizi[idx++] = R[j++];
        }
        s++;
    }
    while (i < (int)L.size()) dizi[idx++] = L[i++];
    while (j < (int)R.size()) dizi[idx++] = R[j++];
}

void mergeSort(vector<Parca>& dizi, int l, int r, long long& k, long long& s) {
    if (l < r) {
        int m = (l + r) / 2;
        mergeSort(dizi, l, m, k, s);
        mergeSort(dizi, m + 1, r, k, s);
        merge(dizi, l, m, r, k, s);
    }
}

// 5. Heap Sort: Belleği verimli kullanır, her durumda O(n log n) garantisi verir
void heapify(vector<Parca>& dizi, int n, int i, long long& k, long long& s) {
    int largest = i;
    int l = 2 * i + 1;
    int r = 2 * i + 2;
    if (l < n) {
        k++;
        if (karsilastir(dizi[largest], dizi[l])) largest = l;
    }
    if (r < n) {
        k++;
        if (karsilastir(dizi[largest], dizi[r])) largest = r;
    }
    if (largest != i) {
        swap(dizi[i], dizi[largest]);
        s++;
        heapify(dizi, n, largest, k, s);
    }
}

void heapSort(vector<Parca>& dizi, long long& k, long long& s) {
    int n = dizi.size();
    for (int i = n / 2 - 1; i >= 0; i--) heapify(dizi, n, i, k, s);
    for (int i = n - 1; i > 0; i--) {
        swap(dizi[0], dizi[i]);
        s++;
        heapify(dizi, i, 0, k, s);
    }
}

// =======================================================
// BÖLÜM 2: KNAPSACK (ÜRETİM PLANLAMA)
// Amaç: Sınırlı kapasitede (mesai) maksimum kârı elde etmek
// =======================================================

// Greedy (Açgözlü) Yaklaşım: Birim zamana en çok kazanç düşen işi seçer.
// Hızlıdır ama her zaman en iyi sonucu (optimal) vermez.
bool oranKarsilastir(const Is& a, const Is& b) {
    return (double)a.kazanc / a.sure > (double)b.kazanc / b.sure;
}

int greedyKnapsackFunc(vector<Is> isler, int kapasite) {
    sort(isler.begin(), isler.end(), oranKarsilastir);
    int toplam = 0;
    int kalan = kapasite;
    for (auto& is : isler) {
        if (is.sure <= kalan) {
            kalan -= is.sure;
            toplam += is.kazanc;
        }
    }
    return toplam;
}

// Dynamic Programming (DP) Yaklaşım: Olası tüm kombinasyonları hesaplar.
// Kesinlikle en iyi (optimal) sonucu verir ama daha fazla işlem gücü ister.
int dpKnapsackFunc(const vector<Is>& isler, int kapasite) {
    int n = (int)isler.size();
    // DP tablosu oluşturuyoruz
    vector<vector<int>> dp(n + 1, vector<int>(kapasite + 1, 0));

    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= kapasite; w++) {
            if (isler[i - 1].sure <= w)
                dp[i][w] = max(dp[i - 1][w], isler[i - 1].kazanc + dp[i - 1][w - isler[i - 1].sure]);
            else
                dp[i][w] = dp[i - 1][w];
        }
    }
    return dp[n][kapasite];
}

// =======================================================
// BÖLÜM 3: DIJKSTRA (LOJİSTİK / EN KISA YOL)
// Amaç: Fabrika içindeki istasyonlar arası en kısa rotayı bulmak
// =======================================================

// 6 düğümlü örnek bir fabrika haritası üzerinde çalışıyoruz
// 0: Depo, 1: Kesim, 2: Montaj, 3: Boya, 4: Paketleme, 5: Yükleme
int getShortestPath(int startNode, int endNode, int* pathOutput, int& pathLen) {
    // Komşuluk Matrisi: İki nokta arasındaki mesafe (0 ise yol yok demek)
    int graph[6][6] = {
        {0, 4, 0, 0, 0, 0}, // Depo'dan gidilebilen yerler
        {4, 0, 8, 0, 0, 0}, // Kesim'den gidilebilen yerler
        {0, 8, 0, 7, 0, 4}, // Montaj...
        {0, 0, 7, 0, 9, 14},// Boya...
        {0, 0, 0, 9, 0, 10},// Paketleme...
        {0, 0, 4, 14, 10, 0}// Yükleme...
    };

    int dist[6];      // Mesafeleri tutar
    int parent[6];    // Rotayı geri kurmak için ebeveynleri tutar
    bool visited[6];  // Ziyaret edilen düğümler

    for(int i=0; i<6; i++) {
        dist[i] = INT_MAX; // Başlangıçta tüm mesafeler sonsuz
        visited[i] = false;
        parent[i] = -1;
    }

    dist[startNode] = 0;

    // En küçük mesafeli düğümü seçip ilerliyoruz (Dijkstra Mantığı)
    for(int count = 0; count < 6 - 1; count++) {
        int min = INT_MAX, u = -1;
        for(int v = 0; v < 6; v++)
            if(!visited[v] && dist[v] <= min) {
                min = dist[v];
                u = v;
            }

        if(u == -1) break;
        visited[u] = true;

        for(int v = 0; v < 6; v++)
            if(!visited[v] && graph[u][v] && dist[u] != INT_MAX && dist[u] + graph[u][v] < dist[v]) {
                dist[v] = dist[u] + graph[u][v];
                parent[v] = u;
            }
    }

    // Rotayı tersten oluşturup düzeltiyoruz
    if(dist[endNode] == INT_MAX) return -1; // Yol yoksa hata dön

    vector<int> path;
    int curr = endNode;
    while(curr != -1) {
        path.push_back(curr);
        curr = parent[curr];
    }
    reverse(path.begin(), path.end());

    // Sonucu pointer ile Python'a gönderiyoruz
    pathLen = path.size();
    for(int i=0; i<pathLen; i++) pathOutput[i] = path[i];

    return dist[endNode];
}

// =======================================================
// BÖLÜM 4: BINARY SEARCH (ARAMA)
// Amaç: Sıralı stok içinde belirli bir parçayı O(log n) ile bulmak
// =======================================================
int binarySearchFunc(const vector<Parca>& dizi, int arananUzunluk) {
    int left = 0, right = (int)dizi.size() - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (dizi[mid].uzunluk == arananUzunluk) return mid; // Bulundu
        if (dizi[mid].uzunluk < arananUzunluk) left = mid + 1;
        else right = mid - 1;
    }
    return -1; // Bulunamadı
}

// =======================================================
// PYTHON API BAĞLANTISI (EXTERN C)
// Python ctypes kütüphanesi bu fonksiyonları çağıracak
// =======================================================
extern "C" {
    struct AnalizSonuclari {
        long long sureMs;
        long long karsilastirma;
        long long swapSayisi;
        long long ayarDegisimi;
        long long toplamMaliyet;
    };

    // 1. Python'dan gelen veriyi sıralar ve analiz eder
    DLLEXPORT void sirala_ve_analiz_et(int* uzunluklar, int* agirliklar, int n, int algoritmaTipi, AnalizSonuclari* sonuc) {
        vector<Parca> parcalar(n);
        // Python dizisini C++ vektörüne çevir
        for(int i=0; i<n; i++) {
            parcalar[i].uzunluk = uzunluklar[i];
            parcalar[i].agirlik = agirliklar[i];
            // Setup süresi için sınıflandırma yapıyoruz
            if (parcalar[i].uzunluk <= 200) parcalar[i].sinif = 0;
            else if (parcalar[i].uzunluk <= 400) parcalar[i].sinif = 1;
            else if (parcalar[i].uzunluk <= 600) parcalar[i].sinif = 2;
            else if (parcalar[i].uzunluk <= 800) parcalar[i].sinif = 3;
            else parcalar[i].sinif = 4;
        }

        long long k = 0, s = 0;
        auto basla = high_resolution_clock::now();

        // Seçilen algoritmaya göre sıralama yap
        switch(algoritmaTipi) {
            case 0: insertionSort(parcalar, k, s); break;
            case 1: shellSort(parcalar, k, s); break;
            case 2: quickSort(parcalar, 0, n - 1, k, s); break;
            case 3: mergeSort(parcalar, 0, n - 1, k, s); break;
            case 4: heapSort(parcalar, k, s); break;
            default: quickSort(parcalar, 0, n - 1, k, s); break;
        }

        auto bitir = high_resolution_clock::now();

        // Maliyet ve ayar değişimi analizi
        long long islemeSuresi = 0, ayarMaliyeti = 0, ayarSayisi = 0;
        int prevClass = -1;

        for (const auto& p : parcalar) {
            islemeSuresi += uretimSuresi(p);
            // Sınıf değişimi kontrolü
            int ceza = ayarDegisimMaliyeti(prevClass, p.sinif);
            if (ceza > 0) ayarSayisi++;
            ayarMaliyeti += ceza;
            prevClass = p.sinif;
        }

        // Sonuçları struct içine yaz
        sonuc->sureMs = duration_cast<milliseconds>(bitir - basla).count();
        sonuc->karsilastirma = k;
        sonuc->swapSayisi = s;
        sonuc->ayarDegisimi = ayarSayisi;
        sonuc->toplamMaliyet = islemeSuresi + ayarMaliyeti;

        // Sıralı veriyi Python'a geri göndermek için diziye yaz
        for(int i=0; i<n; i++) {
            uzunluklar[i] = parcalar[i].uzunluk;
            agirliklar[i] = parcalar[i].agirlik;
        }
    }

    // 2. Knapsack problemi için çağrılır
    DLLEXPORT void optimize_uretim_plani(int* sureler, int* kazanclar, int n, int kapasite, int* sonucGreedy, int* sonucDP) {
        vector<Is> isler(n);
        for(int i=0; i<n; i++) {
            isler[i].sure = sureler[i];
            isler[i].kazanc = kazanclar[i];
        }
        // İki yöntemi de çalıştırıp karşılaştırmak için sonuçları döndürüyoruz
        *sonucGreedy = greedyKnapsackFunc(isler, kapasite);
        *sonucDP = dpKnapsackFunc(isler, kapasite);
    }

    // 3. Dijkstra için çağrılır
    DLLEXPORT int en_kisa_yol_bul(int baslangic, int bitis, int* yolDizisi, int* yolUzunlugu) {
        return getShortestPath(baslangic, bitis, yolDizisi, *yolUzunlugu);
    }

    // 4. Arama için çağrılır
    DLLEXPORT int parca_ara(int* uzunluklar, int n, int aranan) {
        vector<Parca> v(n);
        for(int i=0; i<n; i++) v[i].uzunluk = uzunluklar[i];
        return binarySearchFunc(v, aranan);
    }
}