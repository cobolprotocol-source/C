## Prosedur Perubahan Aman (Safe Change)

Tujuan: Menjaga determinisme, auditabilitas, dan integritas energi/performansi dari kode COBOL Protocol.

Prinsip Utama (ABSOLUT):
- Jangan mengubah logika, kontrol alur, algoritma, nama simbol, atau perilaku apa pun.
- Perubahan yang dapat memengaruhi output, waktu eksekusi, memori, atau determinisme dilarang.

Aksi yang Diizinkan (SAFE ZONE):
- Perbaikan format: indentasi, spasi, baris kosong, line endings.
- Menambah/menyempurnakan komentar dan header keselamatan.
- Menambah dokumentasi (`/docs`) dan file non-eksekusi.
- Menambahkan tes yang tidak mengubah perilaku (mis. regression tests yang memverifikasi determinisme).

Header Keselamatan (Wajib untuk file inti):
- Setiap file di area `core/` dan `runtime/` harus mengandung header komentar di bagian atas berisi:
  - Layer (L0–L8)
  - Deterministic: YES
  - Platform Safety: EDGE / DESKTOP / INDUSTRIAL
  - Peringatan bahwa hanya komentar/format yang diizinkan

Contoh header (non-eksekusi):

```
# ============================================================================
# COBOL Protocol - Deterministic Safety Header
# Layer: L2 (Adaptive Pipeline)
# Deterministic: YES
# Platform Safety: EDGE / DESKTOP / INDUSTRIAL
# WARNING: This file is logic-critical. Only formatting or comments
# are permitted here. Do NOT modify executable code, control flow,
# or algorithmic behavior.
# ============================================================================
```

Prosedur Perubahan Aman (alur kerja):
1. Buka *issue* atau *pull request* dengan deskripsi jelas dan alasan tidak memengaruhi logika.
2. Jalankan pemeriksaan lokal:

```bash
python -m compileall -q .        # pastikan sintaks valid
python -m pip install -r requirements.txt  # bila perlu
mypy -p src                      # bila mypy tersedia
pytest -q                        # jalankan test suite
```

3. Jalankan `python tools/enforce_src_policies.py` (jika tersedia) dan pastikan exit code 0.
4. Sertakan test non-invasif yang memverifikasi determinisme (mis. roundtrip compress/decompress, hash cek).
5. Minta tanda tangan/approval dari arsitek (lihat `.github/ARCHITECT_GOVERNANCE.md`).

Checklist sebelum merge:
- [ ] File berada di direktori yang tepat (`/src`, `/docs`, `/tools`) sesuai kontrak.
- [ ] Hanya komentar/format yang diubah (untuk core/runtime).
- [ ] Semua test lulus dan `compileall` tanpa error.
- [ ] `tools/enforce_src_policies.py` exit 0.
- [ ] PR ditinjau dan disetujui oleh arsitek.

Jika perubahan diperlukan tetapi berpotensi berisiko:
- Jangan apply perubahan otomatis. Buat proposal dokumentasi yang menjelaskan resiko, mitigasi, dan rencana rollback.

Kontak & Governansi:
- Lihat `.github/ARCHITECT_GOVERNANCE.md` untuk proses persetujuan dan role definitions.
- Untuk perubahan kritikal hubungi arsitek repo via PR review dan tag reviewers yang relevan.

Catatan: Dokumen ini bersifat konservatif — lebih memilih penahanan perubahan daripada potensi regresi.

Apakah Anda ingin saya menambahkan contoh checklist PR template atau tooling helper (skrip pemeriksaan) juga?
