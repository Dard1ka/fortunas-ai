import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Icon from '../ui/Icon.jsx';
import Button from '../ui/Button.jsx';
import Card from '../ui/Card.jsx';
import Pill from '../ui/Pill.jsx';
import { api } from '../api/client.js';
import { formatRupiah } from '../lib/format.js';
import { Dialog } from './products/ProductsScreen.jsx';

// Backend MEMBEKUKAN status di 'accepted' saat refund datang setelah UMKM
// menerima — payment_status adalah satu-satunya jejak. (order_models Flutter)
const isRefunded = (o) =>
  ['refund', 'partial_refund', 'chargeback'].includes(String(o.payment_status || '').toLowerCase());

export default function OrdersScreen() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [submittingId, setSubmittingId] = useState(null); // per-kartu, BUKAN per-layar
  const [rejectFor, setRejectFor] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      // Tanpa parameter status → default backend: actionable (paid + accepted).
      const r = await api.listOrders();
      setOrders(r.orders || []);
    } catch (err) {
      setError(err.message || 'Gagal memuat pesanan.');
      setOrders((prev) => prev ?? []);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // NON-optimistis: status bisa berubah dari perangkat/webhook lain, jadi
  // setelah aksi sukses SELALU reload dari server; 409 = kondisi normal.
  const run = async (order, action, failMsg) => {
    setSubmittingId(order.id);
    setError(null);
    setNotice(null);
    try {
      await action(order.id);
      setNotice('Pesanan diperbarui.');
      await load();
    } catch (err) {
      setError(err.message || failMsg);
    } finally {
      setSubmittingId(null);
    }
  };

  const statusPill = (o) => <Pill bg="var(--surface-soft)" sm mono>{o.status}</Pill>;

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Pesanan Masuk" />

      <div style={{ padding: '4px 18px 8px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '0 0 4px' }}>
            Pesanan Masuk
          </h2>
          <p style={{ color: 'var(--ink-3)', fontSize: 12.5, margin: 0 }}>
            Terima pesanan setelah dana masuk kamu cek. Tolak = stok kembali otomatis.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="text" data-testid="orders-back" onClick={() => navigate('/')}>Kembali</Button>
          <Button variant="secondary" data-testid="orders-refresh" onClick={load}>Muat ulang</Button>
        </div>
      </div>

      <div style={{ padding: '0 18px 24px', display: 'grid', gap: 10 }}>
        {notice && (
          <div role="status" style={{ padding: '10px 14px', background: 'var(--lime)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
            {notice}
          </div>
        )}
        {error && (
          <div role="alert" style={{ padding: '10px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
            {error}
          </div>
        )}

        {orders == null && <div style={{ textAlign: 'center', padding: 32, color: 'var(--ink-3)', fontSize: 13 }}>Memuat…</div>}

        {orders != null && orders.length === 0 && !error && (
          <div data-testid="orders-empty" style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--ink-3)' }}>
            <Icon name="bag" size={34} stroke="var(--ink-4)" />
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink-2)', marginTop: 10 }}>Belum ada pesanan masuk.</div>
            <div style={{ fontSize: 12.5, marginTop: 4 }}>Bagikan kode tokomu ke pelanggan untuk mulai menerima pesanan.</div>
          </div>
        )}

        {(orders || []).map((o) => {
          const busy = submittingId === o.id;
          return (
            <Card key={o.id} style={{ display: 'grid', gap: 8, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 14 }}>
                  {o.customer_name || 'Pelanggan'}
                </span>
                {statusPill(o)}
              </div>

              {isRefunded(o) && (
                <div data-testid={`orders-refunded-${o.id}`} style={{ padding: '8px 10px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 10, fontSize: 12 }}>
                  ⚠ Dana sudah dikembalikan ke pelanggan ({o.payment_status})
                </div>
              )}

              <div style={{ display: 'grid', gap: 3 }}>
                {(o.items || []).map((it, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--ink-2)' }}>
                    <span>{it.qty}× {it.name}</span>
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{formatRupiah(it.subtotal)}</span>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px dashed var(--border-soft)', paddingTop: 8, fontWeight: 700, fontSize: 13.5 }}>
                <span>Total</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>{formatRupiah(o.total)}</span>
              </div>

              {o.status === 'paid' && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button
                    data-testid={`orders-accept-${o.id}`}
                    disabled={busy}
                    onClick={() => run(o, api.acceptOrder, 'Gagal menerima pesanan.')}
                    style={{ flex: 1 }}
                  >
                    {busy ? 'Memproses…' : 'Terima'}
                  </Button>
                  <Button
                    data-testid={`orders-reject-${o.id}`}
                    variant="secondary"
                    disabled={busy}
                    onClick={() => setRejectFor(o)}
                    style={{ flex: 1 }}
                  >
                    Tolak
                  </Button>
                </div>
              )}
              {o.status === 'accepted' && (
                <Button
                  data-testid={`orders-complete-${o.id}`}
                  disabled={busy}
                  onClick={() => run(o, api.completeOrder, 'Gagal menyelesaikan pesanan.')}
                >
                  {busy ? 'Memproses…' : 'Selesai'}
                </Button>
              )}
            </Card>
          );
        })}
      </div>

      {rejectFor && (
        <Dialog title="Tolak pesanan?" onClose={() => setRejectFor(null)}>
          <div style={{ fontSize: 12.5, color: 'var(--ink-2)' }}>
            Stok {rejectFor.items.length} item akan dikembalikan otomatis. Pengembalian uang ke
            pelanggan harus kamu lakukan manual.
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button variant="text" onClick={() => setRejectFor(null)}>Batal</Button>
            <Button
              onClick={() => {
                const o = rejectFor;
                setRejectFor(null);
                run(o, api.rejectOrder, 'Gagal menolak pesanan.');
              }}
              style={{ background: 'var(--error)' }}
            >
              Tolak Pesanan
            </Button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
