import re
import random
import bisect
from collections import deque, defaultdict
from typing import List, Deque


class TextQuilter:
    def __init__(self, teks_sumber: str, kapasitas_memori: int = 5, panjang_patch: int = 5):
        self.panjang_patch = panjang_patch
        self.kapasitas_memori = kapasitas_memori

        # Preprocessing
        self.tokens = self._preprocess(teks_sumber)

        # Index posisi kata (sekali saja)
        self.posisi_kata = defaultdict(list)
        for i, t in enumerate(self.tokens):
            self.posisi_kata[t].append(i)

        # Patches
        self.patches = self._buat_patches()

        # Precompute kata bermakna per patch
        self.patch_meaningful = [self._kata_bermakna(p) for p in self.patches]

        # Map kata awal → patch index
        self.patch_map = defaultdict(list)
        for idx, p in enumerate(self.patches):
            self.patch_map[p[0]].append(idx)

        # Cache proximity
        self.cache_dekat = {}

        # Memori
        self.memori: Deque[str] = self._init_memori()
        self.memori_set = set(self.memori)

        print(f"Total tokens: {len(self.tokens)}")
        print(f"Total patches: {len(self.patches)}")
        print(f"Memori awal: {list(self.memori)}")

    def _preprocess(self, teks: str) -> List[str]:
        teks = teks.lower()
        teks = re.sub(r'([.,!?;:])', r' \1 ', teks)
        teks = re.sub(r'["\']', '', teks)
        teks = re.sub(r'\s+', ' ', teks).strip()
        return teks.split()

    def _buat_patches(self) -> List[List[str]]:
        return [
            self.tokens[i:i + self.panjang_patch]
            for i in range(len(self.tokens) - self.panjang_patch + 1)
        ]

    def _init_memori(self) -> Deque[str]:
        tanda = {'.', ',', '!', '?', ';', ':'}
        kata = [t for t in self.tokens if t not in tanda]

        if len(kata) < self.kapasitas_memori:
            return deque(kata)

        return deque(random.sample(kata, self.kapasitas_memori))

    def _kata_bermakna(self, tokens: List[str]) -> List[str]:
        tanda = {'.', ',', '!', '?', ';', ':'}
        return [t for t in tokens if t not in tanda]

    def _hitung_skor_memori(self, patch_idx: int) -> int:
        patch = self.patches[patch_idx]
        return sum(1 for k in patch if k in self.memori_set)

    def _cari_kata_dekat(self, patch_idx: int, window: int = 10) -> int:
        # Cache
        if patch_idx in self.cache_dekat:
            return self.cache_dekat[patch_idx]

        skor = 0
        kata_patch = set(self.patch_meaningful[patch_idx])

        for kata_memori in self.memori:
            posisi_mem = self.posisi_kata.get(kata_memori, [])
            if not posisi_mem:
                continue

            for kata_p in kata_patch:
                posisi_p = self.posisi_kata.get(kata_p, [])
                if not posisi_p:
                    continue

                for pm in posisi_mem:
                    i = bisect.bisect_left(posisi_p, pm)

                    if i > 0 and abs(posisi_p[i - 1] - pm) <= window:
                        self.cache_dekat[patch_idx] = 1
                        return 1
                    if i < len(posisi_p) and abs(posisi_p[i] - pm) <= window:
                        self.cache_dekat[patch_idx] = 1
                        return 1

        self.cache_dekat[patch_idx] = 0
        return 0

    def _pilih_kata_dari_buffer_dengan_bias(self, buffer_tokens: List[str]) -> str:
        kata = self._kata_bermakna(buffer_tokens)
        if not kata:
            return None

        n = len(kata)
        if n <= 2:
            return random.choice(kata)

        bobot = [1.0 - (0.4 * min(i, n - 1 - i) / (n // 2)) for i in range(n)]
        return random.choices(kata, weights=bobot)[0]

    def _cari_patch_jahitan(self, kata_akhir: str) -> List[int]:
        return self.patch_map.get(kata_akhir, [])

    def _update_memori(self, buffer_tokens: List[str]):
        # Cari kata baru yang valid (tidak duplikat)
        for _ in range(15):
            kata_baru = self._pilih_kata_dari_buffer_dengan_bias(buffer_tokens)
            if (
                kata_baru
                and kata_baru not in self.memori_set
                and len(kata_baru) > 3
            ):
                if len(self.memori) >= self.kapasitas_memori:
                    old = self.memori.popleft()
                    self.memori_set.remove(old)

                self.memori.append(kata_baru)
                self.memori_set.add(kata_baru)
                return
        # fallback: tidak update jika gagal cari kata baru

    def jahit(self, target_panjang: int = 200) -> str:
        if not self.patches:
            return "Teks kosong."

        buffer_tokens = self.patches[random.randrange(len(self.patches))].copy()
        max_extend = len(self.patches[0])

        while len(buffer_tokens) < target_panjang:
            kata_akhir = buffer_tokens[-1]
            kandidat = self._cari_patch_jahitan(kata_akhir)

            if not kandidat:
                break

            # LIMIT kandidat (opsional tapi penting di dataset besar)
            if len(kandidat) > 200:
                kandidat = random.sample(kandidat, 200)

            # Level 1
            skor_mem = [(idx, self._hitung_skor_memori(idx)) for idx in kandidat]
            max_s = max(s for _, s in skor_mem)

            if max_s > 0:
                terbaik = [idx for idx, s in skor_mem if s == max_s]
                chosen = random.choice(terbaik)
            else:
                # Level 2
                skor_dekat = [(idx, self._cari_kata_dekat(idx)) for idx in kandidat]
                max_d = max(s for _, s in skor_dekat)

                if max_d > 0:
                    terbaik = [idx for idx, s in skor_dekat if s == max_d]
                    chosen = random.choice(terbaik)
                else:
                    chosen = random.choice(kandidat)

            patch = self.patches[chosen]

            buffer_tokens.extend(
                patch[1:random.randint(2, max_extend)]
            )

            self._update_memori(buffer_tokens)

        teks = ' '.join(buffer_tokens)
        return re.sub(r'\s+([.,!?;:])', r'\1', teks)


if __name__ == "__main__":
    with open('bahan.txt', 'r', encoding='utf-8') as f:
        teks_sumber = f.read()

    quilter = TextQuilter(teks_sumber, kapasitas_memori=5, panjang_patch=7)
    hasil = quilter.jahit(target_panjang=100)
    print(hasil)
