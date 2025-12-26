cmake_minimum_required(VERSION 3.20)
project(AlgorithmProject)

set(CMAKE_CXX_STANDARD 17)

# --- KRİTİK AYARLAR (STATIC LINKING) ---
# Bu ayarlar, DLL'in başka dosyalara ihtiyaç duymadan tek başına çalışmasını sağlar.
set(CMAKE_CXX_FLAGS "-static")
set(CMAKE_EXE_LINKER_FLAGS "-static")
set(CMAKE_SHARED_LINKER_FLAGS "-static")

add_library(optimization_engine SHARED main.cpp)