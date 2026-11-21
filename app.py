import os
from datetime import date

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from forms import PILIHAN_KATEGORI, BookingForm, EventForm

app = Flask(__name__)

# Kunci untuk sesi, flash message, dan token CSRF Flask-WTF (Pertemuan 12)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "riuh-kunci-dev-ganti-nanti")
app.config["WTF_CSRF_ENABLED"] = True

# Data sementara di list Python, nanti diganti database
EVENTS = [
    {"id": 1, "nama": "Vacations: Holy Grail Tour", "lokasi": "Bengkel Space, SCBD, Jakarta",
     "tanggal": date(2026, 7, 9), "harga": 399000, "kuota": 500, "stok": 67},
    {"id": 2, "nama": "Kanye West: YE Live in Jakarta", "lokasi": "Stadion Utama GBK, Jakarta",
     "tanggal": date(2026, 10, 24), "harga": 1875000, "kuota": 1000, "stok": 666},
    {"id": 3, "nama": "My Chemical Romance: Live in Jakarta", "lokasi": "Jakarta International Stadium, Jakarta",
     "tanggal": date(2026, 11, 22), "harga": 1059000, "kuota": 100, "stok": 10},
]
BOOKINGS = []

# Harga VIP dua kali lipat harga Festival
PENGALI_HARGA = {"festival": 1, "vip": 2}

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
         "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


@app.template_filter("rupiah")
def rupiah(angka):
    return "Rp" + f"{angka:,}".replace(",", ".")


@app.template_filter("tanggal")
def tanggal(tgl):
    return f"{tgl.day} {BULAN[tgl.month - 1]} {tgl.year}"


@app.template_filter("bulan")
def bulan(tgl):
    return BULAN[tgl.month - 1].upper()


def urut_event():
    return sorted(EVENTS, key=lambda e: e["tanggal"])


def cari_event(event_id):
    return next((e for e in EVENTS if e["id"] == event_id), None)


@app.route("/")
def index():
    return render_template("index.html", events=urut_event())


# Form publik: GET menampilkan form, POST memproses (Pertemuan 12)
@app.route("/booking", methods=["GET", "POST"])
def booking():
    tersedia = [e for e in urut_event() if e["stok"] > 0]
    # tombol "Beli Tiket" di beranda mengirim ?event=id supaya event langsung terpilih
    form = BookingForm(tersedia, event=request.args.get("event", type=int))

    if form.validate_on_submit():
        event = cari_event(form.event.data)
        jumlah = form.jumlah.data
        kategori = form.kategori.data
        kode = f"RIUH-{len(BOOKINGS) + 1:04d}"

        event["stok"] -= jumlah
        BOOKINGS.append({
            "kode": kode,
            "nama": form.nama.data.strip(),
            "email": form.email.data.strip(),
            "event_nama": event["nama"],
            "lokasi": event["lokasi"],
            "tanggal": event["tanggal"],
            "kategori": dict(PILIHAN_KATEGORI)[kategori],
            "jumlah": jumlah,
            "total": event["harga"] * PENGALI_HARGA[kategori] * jumlah,
        })

        flash(f"Booking berhasil! Kode pesananmu {kode}.", "success")
        # PRG: setelah POST sukses, redirect ke halaman GET supaya aman di-refresh
        return redirect(url_for("tiket", kode=kode))

    return render_template("booking.html", form=form, tersedia=tersedia)


@app.route("/tiket/<kode>")
def tiket(kode):
    pesanan = next((b for b in BOOKINGS if b["kode"] == kode), None)
    if pesanan is None:
        abort(404)
    return render_template("tiket.html", pesanan=pesanan)


# Dashboard admin sekaligus form tambah event
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    form = EventForm()

    if form.validate_on_submit():
        EVENTS.append({
            "id": max((e["id"] for e in EVENTS), default=0) + 1,
            "nama": form.nama.data.strip(),
            "lokasi": form.lokasi.data.strip(),
            "tanggal": form.tanggal.data,
            "harga": form.harga.data,
            "kuota": form.kuota.data,
            "stok": form.kuota.data,
        })
        flash(f'Event "{form.nama.data.strip()}" berhasil ditambahkan.', "success")
        return redirect(url_for("admin_dashboard"))   # PRG

    terjual = sum(b["jumlah"] for b in BOOKINGS)
    pendapatan = sum(b["total"] for b in BOOKINGS)
    statistik = [
        {"label": "Total Event", "nilai": len(EVENTS), "ket": "konser aktif", "warna": "kuning"},
        {"label": "Tiket Terjual", "nilai": terjual, "ket": f"dari {len(BOOKINGS)} pesanan", "warna": "mint"},
        {"label": "Pendapatan", "nilai": rupiah(pendapatan), "ket": "dari semua pesanan", "warna": "pink"},
        {"label": "Sisa Stok", "nilai": sum(e["stok"] for e in EVENTS), "ket": "tiket tersedia", "warna": "biru"},
    ]
    return render_template("admin.html", form=form, statistik=statistik,
                           events=urut_event(), bookings=BOOKINGS)


@app.errorhandler(404)
def tidak_ditemukan(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
