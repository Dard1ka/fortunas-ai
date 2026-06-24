# Ringkasan

<!-- Apa yang diubah & kenapa, 1-2 kalimat. -->

## Jenis perubahan
- [ ] Fitur baru
- [ ] Bugfix
- [ ] Refactor / cleanup
- [ ] Docs
- [ ] CI / infra

## Cara test

<!-- Command yang dijalankan + hasilnya. -->

```bash
python -m pytest tests/ -v
cd mobile && flutter analyze --no-fatal-infos
```

## Checklist
- [ ] CI hijau (ruff + pytest + flutter analyze)
- [ ] Alur lama tidak rusak (voice/checkout, auth web)
- [ ] Mengikuti kontrak di `docs/API_CONTRACTS.md` (kalau menyentuh schema/endpoint)
- [ ] Tidak ada secret/credential ter-commit
- [ ] Docs di-update kalau perlu
- [ ] Handoff `docs/handoff/day-XX.md` ditulis (kalau hari rotasi)
