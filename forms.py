from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, EmailField, IntegerField, SelectField, StringField
from wtforms.validators import (DataRequired, Email, InputRequired, Length,
                                NumberRange, Regexp, ValidationError)

PILIHAN_KATEGORI = [
    ("", "Pilih kategori..."),
    ("festival", "Festival"),
    ("vip", "VIP"),
]


class BookingForm(FlaskForm):
    nama = StringField("Nama Lengkap", validators=[
        DataRequired(message="Nama lengkap wajib diisi."),
        Length(min=3, max=50, message="Nama harus 3 sampai 50 karakter."),
        Regexp(r"^[A-Za-z][A-Za-z .'-]*$",
               message="Nama hanya boleh berisi huruf dan spasi."),
    ])
    email = EmailField("Email", validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid."),
    ])
    event = SelectField("Pilih Event", coerce=int, validators=[
        DataRequired(message="Pilih event yang ingin ditonton."),
    ])
    kategori = SelectField("Kategori Tiket", choices=PILIHAN_KATEGORI, validators=[
        DataRequired(message="Pilih kategori tiket."),
    ])
    jumlah = IntegerField("Jumlah Tiket", default=1, validators=[
        InputRequired(message="Jumlah tiket wajib diisi."),
        NumberRange(min=1, max=10, message="Jumlah tiket 1 sampai 10 per transaksi."),
    ])

    def __init__(self, events, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pilihan event diisi dari data yang stoknya masih ada
        self.events = {e["id"]: e for e in events}
        self.event.choices = [(0, "Pilih event...")] + [
            (e["id"], e["nama"]) for e in events
        ]

    # validator kustom: jumlah tidak boleh melebihi stok event yang dipilih
    def validate_jumlah(self, field):
        event = self.events.get(self.event.data)
        if event and field.data is not None and field.data > event["stok"]:
            raise ValidationError(f"Stok tidak cukup, sisa {event['stok']} tiket.")


class EventForm(FlaskForm):
    nama = StringField("Nama Event / Artis", validators=[
        DataRequired(message="Nama event wajib diisi."),
        Length(min=3, max=60, message="Nama event harus 3 sampai 60 karakter."),
    ])
    lokasi = StringField("Lokasi / Venue", validators=[
        DataRequired(message="Lokasi wajib diisi."),
        Length(min=3, max=50, message="Lokasi harus 3 sampai 50 karakter."),
    ])
    tanggal = DateField("Tanggal Konser", format="%d/%m/%Y", validators=[
        InputRequired(message="Tanggal konser wajib diisi."),
    ])
    harga = IntegerField("Harga Tiket (Rp)", validators=[
        InputRequired(message="Harga tiket wajib diisi."),
        NumberRange(min=10000, max=5000000,
                    message="Harga tiket Rp10.000 sampai Rp5.000.000."),
    ])
    kuota = IntegerField("Kuota Stok Tiket", validators=[
        InputRequired(message="Kuota tiket wajib diisi."),
        NumberRange(min=1, max=100000, message="Kuota tiket 1 sampai 100.000."),
    ])

    def validate_tanggal(self, field):
        # kalau formatnya salah, data kosong: ganti pesan bawaan WTForms
        if field.data is None:
            field.errors[:] = []
            raise ValidationError("Format tanggal harus dd/mm/yyyy, contoh 25/12/2026.")
        if field.data < date.today():
            raise ValidationError("Tanggal konser tidak boleh sudah lewat.")
