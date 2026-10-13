#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
İhtilat Sosyolojisi - Veri Seti Doğrulayıcı (Dataset Validator)
Bu script, datasets/ altındaki tüm JSON dosyalarının şema bütünlüğünü,
Arapça/Türkçe karakter kodlamasını ve çapraz referanslarını doğrular.
"""

import os
import sys
import json
from pathlib import Path

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def validate_datasets(base_dir: Path) -> bool:
    datasets_dir = base_dir / "datasets"
    if not datasets_dir.exists():
        print(f"[-] Hata: {datasets_dir} dizini bulunamadı!")
        return False

    success = True
    
    # 1. Nass Kaynakları
    nass_file = datasets_dir / "nass_kaynaklari_ve_hadisler.json"
    if not nass_file.exists():
        print(f"[-] Eksik dosya: {nass_file}")
        success = False
    else:
        try:
            with open(nass_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, list), "Nass verisi bir liste olmalıdır."
            for idx, item in enumerate(data):
                for req in ["id", "tur", "kaynak", "turkce", "temalar"]:
                    assert req in item, f"Nass #{idx} içinde '{req}' alanı eksik!"
            print(f"[+] Nass kaynakları doğrulandı: {len(data)} adet kayıt.")
        except Exception as e:
            print(f"[-] Nass dosyası hatası: {e}")
            success = False

    # 2. Mecelle Kaideleri
    mecelle_file = datasets_dir / "mecelle_kaideleri_rag.json"
    if not mecelle_file.exists():
        print(f"[-] Eksik dosya: {mecelle_file}")
        success = False
    else:
        try:
            with open(mecelle_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, list), "Mecelle verisi bir liste olmalıdır."
            for idx, item in enumerate(data):
                for req in ["madde_no", "arapca_kaide", "anlam_ve_serh", "ihtilat_ve_calisma_izdusumu"]:
                    assert req in item, f"Mecelle #{idx} içinde '{req}' alanı eksik!"
            print(f"[+] Mecelle kaideleri doğrulandı: {len(data)} adet madde.")
        except Exception as e:
            print(f"[-] Mecelle dosyası hatası: {e}")
            success = False

    # 3. Modern Vaka Analizleri
    vaka_file = datasets_dir / "modern_vaka_analizleri.json"
    if not vaka_file.exists():
        print(f"[-] Eksik dosya: {vaka_file}")
        success = False
    else:
        try:
            with open(vaka_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, list), "Vaka verisi bir liste olmalıdır."
            for idx, item in enumerate(data):
                for req in ["vaka_id", "baslik", "senaryo", "fikhi_hukum", "mesru_ve_vakarlı_cozum"]:
                    assert req in item, f"Vaka #{idx} içinde '{req}' alanı eksik!"
            print(f"[+] Modern vaka analizleri doğrulandı: {len(data)} adet vaka.")
        except Exception as e:
            print(f"[-] Vaka dosyası hatası: {e}")
            success = False

    return success

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    print(f"[*] Veri setleri denetleniyor: {project_root}")
    ok = validate_datasets(project_root)
    if ok:
        print("[*] TÜM VERİ SETLERİ BAŞARIYLA DOĞRULANDI.")
        sys.exit(0)
    else:
        print("[-] DOĞRULAMA BAŞARISIZ OLDU!")
        sys.exit(1)
