"""
Sample documents for fallback/testing when web scraping is not configured.

PURPOSE / TUJUAN:
- EN: Provides a curated set of sample documents covering various topics (programming, AI, Indonesia, general knowledge, tech).
  These are used as fallback when SCRAPE_URLS is empty or web scraping fails.
- ID: Menyediakan serangkaian dokumen sampel yang dikurasi mencakup berbagai topik (pemrograman, AI, Indonesia, pengetahuan umum, teknologi).
  Ini digunakan sebagai fallback ketika SCRAPE_URLS kosong atau web scraping gagal.

TOPICS COVERED / TOPIK YANG DIBAHAS:
- Programming languages & tools / Bahasa dan alat pemrograman
- AI & Machine Learning concepts / Konsep AI & Machine Learning
- Indonesian geography & culture / Geografi dan budaya Indonesia
- General knowledge / Pengetahuan umum
- Cloud & DevOps technologies / Teknologi Cloud & DevOps

USE CASE / KASUS PENGGUNAAN:
- Development & testing without requiring live web scraping / Pengembangan & pengujian tanpa memerlukan web scraping langsung
- Demonstration of RAG system functionality / Demonstrasi fungsionalitas sistem RAG
- Fallback when network/scraping configuration is unavailable / Fallback ketika konfigurasi jaringan/scraping tidak tersedia
"""

from typing import List

documents: List[str] = [
    # Programming
    """Sumber: fallback
Judul: Python untuk Data Science

Python adalah bahasa pemrograman yang populer untuk data science dan web development""",
    
    """Sumber: fallback
Judul: JavaScript untuk Web

JavaScript digunakan untuk membuat aplikasi web interaktif""",
    
    """Sumber: fallback
Judul: Git Version Control

Git adalah sistem version control untuk melacak perubahan kode""",
    
    """Sumber: fallback
Judul: Apa itu API

API adalah cara agar dua sistem bisa saling berkomunikasi""",

    # AI & Technology
    """Sumber: fallback
Judul: Pengertian AI

AI adalah kecerdasan buatan yang meniru kemampuan manusia""",
    
    """Sumber: fallback
Judul: Machine Learning Basics

Machine Learning adalah cabang AI yang belajar dari data""",
    
    """Sumber: fallback
Judul: Deep Learning Explained

Deep Learning menggunakan neural network untuk memproses data kompleks""",
    
    """Sumber: fallback
Judul: RAG Technology

RAG adalah teknik yang menggabungkan pencarian dan generasi teks""",

    # Indonesia
    """Sumber: fallback
Judul: Jakarta - Ibu Kota Indonesia

Jakarta adalah ibu kota Indonesia""",
    
    """Sumber: fallback
Judul: Indonesia Negara Kepulauan

Indonesia adalah negara kepulauan terbesar di dunia""",
    
    """Sumber: fallback
Judul: Bahasa Indonesia

Bahasa Indonesia adalah bahasa resmi Indonesia""",
    
    """Sumber: fallback
Judul: Bali Destinasi Wisata

Bali adalah destinasi wisata terkenal di Indonesia""",

    # General Knowledge
    """Sumber: fallback
Judul: Matahari dan Tata Surya

Matahari adalah pusat tata surya""",
    
    """Sumber: fallback
Judul: Suhu Air Mendidih

Air mendidih pada suhu 100 derajat Celsius""",
    
    """Sumber: fallback
Judul: Kebutuhan Manusia akan Oksigen

Manusia membutuhkan oksigen untuk bernapas""",
    
    """Sumber: fallback
Judul: Rotasi Bumi

Bumi mengelilingi matahari dalam 365 hari""",

    # Tech Concepts
    """Sumber: fallback
Judul: Database Systems

Database digunakan untuk menyimpan dan mengelola data""",
    
    """Sumber: fallback
Judul: SQL Query Language

SQL adalah bahasa untuk mengakses database""",
    
    """Sumber: fallback
Judul: Docker Containers

Docker digunakan untuk membuat container aplikasi""",
    
    """Sumber: fallback
Judul: Kubernetes Orchestration

Kubernetes digunakan untuk mengelola container dalam skala besar""",
]
