// Smart Retail JavaScript
const formatRupiah = (n) => new Intl.NumberFormat('id-ID', {style: 'currency', currency: 'IDR', minimumFractionDigits: 0}).format(n);

function updateKeranjang() {
    fetch('/api/get_keranjang')
        .then(r => r.json())
        .then(data => {
            document.getElementById('displayTotal').innerText = formatRupiah(data.total_bayar);
            document.getElementById('badgeJumlahItem').innerText = data.total_items + ' Item';
        });
}

setInterval(updateKeranjang, 1000);
