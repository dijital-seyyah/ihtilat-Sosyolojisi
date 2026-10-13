#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
İhtilat Sosyolojisi - Fıkhî RAG & Arama Motoru (Fiqh Retrieval-Augmented Generation Engine)

Bu araç:
1. Nass (Ayet/Hadis), Mecelle kaideleri ve modern vaka veri setlerini belleğe yükler.
2. Anahtar kelime ve anlamsal eşleşmeyle fıkhî hükümleri ve sosyolojik analizleri sorgular.
3. LLM'ler (Claude, GPT, Gemini vb.) için optimize edilmiş RAG sistem istemi (prompt context) üretir.
4. Modern vaka analizi raporu çıkarır.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class FiqhRAGEngine:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.datasets_dir = base_dir / "datasets"
        self.nass_data: List[Dict[str, Any]] = []
        self.mecelle_data: List[Dict[str, Any]] = []
        self.vaka_data: List[Dict[str, Any]] = []
        self._load_datasets()

    def _load_datasets(self):
        nass_path = self.datasets_dir / "nass_kaynaklari_ve_hadisler.json"
        mecelle_path = self.datasets_dir / "mecelle_kaideleri_rag.json"
        vaka_path = self.datasets_dir / "modern_vaka_analizleri.json"

        if nass_path.exists():
            with open(nass_path, "r", encoding="utf-8") as f:
                self.nass_data = json.load(f)
        if mecelle_path.exists():
            with open(mecelle_path, "r", encoding="utf-8") as f:
                self.mecelle_data = json.load(f)
        if vaka_path.exists():
            with open(vaka_path, "r", encoding="utf-8") as f:
                self.vaka_data = json.load(f)

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        q_tokens = query.lower().split()
        
        def match_score(text: str) -> int:
            t = text.lower()
            return sum(1 for tok in q_tokens if tok in t)

        results = {
            "query": query,
            "nass": [],
            "mecelle": [],
            "vakalar": []
        }

        # Nass araması
        scored_nass = []
        for item in self.nass_data:
            corpus = f"{item.get('kaynak','')} {item.get('turkce','')} {item.get('baglam_ve_serh','')} {' '.join(item.get('temalar',[]))} {item.get('modern_uygulama','')}"
            score = match_score(corpus)
            if score > 0:
                scored_nass.append((score, item))
        scored_nass.sort(key=lambda x: x[0], reverse=True)
        results["nass"] = [item for _, item in scored_nass[:limit]]

        # Mecelle araması
        scored_mecelle = []
        for item in self.mecelle_data:
            corpus = f"{item.get('madde_no','')} {item.get('arapca_kaide','')} {item.get('anlam_ve_serh','')} {item.get('ihtilat_ve_calisma_izdusumu','')} {' '.join(item.get('keywords',[]))}"
            score = match_score(corpus)
            if score > 0:
                scored_mecelle.append((score, item))
        scored_mecelle.sort(key=lambda x: x[0], reverse=True)
        results["mecelle"] = [item for _, item in scored_mecelle[:limit]]

        # Vaka araması
        scored_vaka = []
        for item in self.vaka_data:
            corpus = f"{item.get('vaka_id','')} {item.get('baslik','')} {item.get('senaryo','')} {item.get('modernist_savunma','')} {item.get('sosyolojik_ve_kalbi_tahribat','')} {item.get('fikhi_hukum','')}"
            score = match_score(corpus)
            if score > 0:
                scored_vaka.append((score, item))
        scored_vaka.sort(key=lambda x: x[0], reverse=True)
        results["vakalar"] = [item for _, item in scored_vaka[:limit]]

        return results

    def generate_prompt_context(self, query: str) -> str:
        results = self.search(query, limit=3)
        context_parts = [
            f"# RAG FIKHÎ BİLGİ TABANI BAĞLAMI",
            f"Kullanıcı Sorusu/Konu: \"{query}\"\n",
            "## 1. İLGİLİ NASSLAR (AYET VE SAHİH HADİSLER):"
        ]

        if not results["nass"]:
            context_parts.append("- Doğrudan eşleşen nass kaydı bulunamadı (Genel sedd-i zerai kaideleri geçerlidir).")
        else:
            for item in results["nass"]:
                context_parts.append(
                    f"[{item['id']}] {item['kaynak']} ({item['tur'].upper()}):\n"
                    f"  Metin: {item['turkce']}\n"
                    f"  Şerh: {item['baglam_ve_serh']}\n"
                    f"  Modern İzdüşüm: {item['modern_uygulama']}\n"
                )

        context_parts.append("## 2. İLGİLİ MECELLE-İ AHKÂM-I ADLİYE KAİDELERİ:")
        if not results["mecelle"]:
            context_parts.append("- Doğrudan eşleşen külli kaide bulunamadı.")
        else:
            for item in results["mecelle"]:
                context_parts.append(
                    f"[Madde {item['madde_no']}] {item['arapca_kaide']}:\n"
                    f"  Açıklama: {item['anlam_ve_serh']}\n"
                    f"  Çalışma Hayatı Analizi: {item['ihtilat_ve_calisma_izdusumu']}\n"
                )

        context_parts.append("## 3. İLGİLİ MODERN VAKA ANALİZLERİ:")
        if not results["vakalar"]:
            context_parts.append("- Doğrudan eşleşen vaka kaydı bulunamadı.")
        else:
            for item in results["vakalar"]:
                context_parts.append(
                    f"[{item['vaka_id']}] {item['baslik']}:\n"
                    f"  Senaryo: {item['senaryo']}\n"
                    f"  Modernist Savunma: {item['modernist_savunma']}\n"
                    f"  Fıkhî Hüküm: {item['fikhi_hukum']}\n"
                    f"  Vakarlı Çözüm Yolu: {item['mesru_ve_vakarlı_cozum']}\n"
                )

        context_parts.append(
            "\n[TALİMAT: Cevap verirken modernitenin sentezci ve modernist tevillerini reddet. "
            "Klasik fıkhın nasslarını, Mecelle'nin kaidelerini ve yukarıdaki fıkhî hükümleri esas al.]"
        )
        return "\n".join(context_parts)

    def print_stats(self):
        print("="*60)
        print("İHTİLAT SOSYOLOJİSİ - BİLGİ TABANI İSTATİSTİKLERİ")
        print("="*60)
        print(f"Toplam Nass (Ayet/Hadis) Kaydı : {len(self.nass_data)}")
        print(f"Toplam Mecelle Kaidesi         : {len(self.mecelle_data)}")
        print(f"Toplam Modern Vaka İncelemesi : {len(self.vaka_data)}")
        print(f"Depo Konumu                   : {self.base_dir}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="İhtilat Sosyolojisi Fıkhî RAG Motoru")
    subparsers = parser.add_subparsers(dest="command", help="Komutlar")

    # Search komutu
    search_parser = subparsers.add_parser("search", help="Fıkhi bilgi tabanında arama yap")
    search_parser.add_argument("query", type=str, help="Aranacak anahtar kelimeler")
    search_parser.add_argument("--limit", type=int, default=3, help="Maksimum sonuç sayısı")

    # Prompt komutu
    prompt_parser = subparsers.add_parser("prompt", help="LLM için RAG prompt bağlamı oluştur")
    prompt_parser.add_argument("query", type=str, help="Sorulacak soru veya konu")

    # Case komutu
    case_parser = subparsers.add_parser("case", help="Belirli bir vakayı incele")
    case_parser.add_argument("vaka_id", type=str, help="Vaka ID (örn: VAKA-001) veya anahtar kelime")

    # Stats komutu
    subparsers.add_parser("stats", help="Bilgi tabanı istatistiklerini göster")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    engine = FiqhRAGEngine(project_root)

    if args.command == "search":
        res = engine.search(args.query, limit=args.limit)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "prompt":
        prompt_ctx = engine.generate_prompt_context(args.query)
        print(prompt_ctx)
    elif args.command == "case":
        v_results = [v for v in engine.vaka_data if args.vaka_id.lower() in v["vaka_id"].lower() or args.vaka_id.lower() in v["baslik"].lower()]
        if not v_results:
            print(f"[-] '{args.vaka_id}' ile eşleşen vaka bulunamadı.")
        else:
            print(json.dumps(v_results, ensure_ascii=False, indent=2))
    elif args.command == "stats" or not args.command:
        engine.print_stats()


if __name__ == "__main__":
    main()
