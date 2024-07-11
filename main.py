import cv2  # Import Library OpenCV untuk pengolahan citra dan video
import face_recognition  # Import library face_recognition untuk pengenalan wajah
import os  # Import Library os untuk interaksi dengan sistem file dan direktori
from datetime import datetime  # Import kelas datetime untuk manipulasi tanggal dan waktu
import pygame  # Import Library Pygame untuk membuat game dan aplikasi multimedia
import pandas as pd  # Import Library Pandas untuk manipulasi dan analisis data
import matplotlib.pyplot as plt  # Import Library Matplotlib untuk visualisasi data

# Inisialisasi mixer Pygame untuk memutar suara
pygame.mixer.init()

# Inisialisasi
path = 'orang'  # Direktori tempat gambar list orang disimpan
images = []  # List untuk menyimpan gambar
classNames = []  # List untuk menyimpan nama kelas (nama orang)
images_without_faces = 0  # Penghitung untuk gambar tanpa wajah
images_with_multiple_faces = 0  # Penghitung untuk gambar dengan lebih dari satu wajah

# Mendapatkan daftar file dalam direktori 'orang'
personsList = os.listdir(path)

# Periksa apakah direktori 'orang' kosong
if not personsList:
    print("\nPeringatan: Folder 'orang' tidak berisi gambar, mohon input terlebih dahulu. Program berhenti.\n")
    exit()

# Proses setiap gambar dalam direktori 'orang'
for cl in personsList:
    curPersonn = cv2.imread(f'{path}/{cl}')  # Baca gambar

    curPersonnRGB = cv2.cvtColor(curPersonn, cv2.COLOR_BGR2RGB)  # Konversi gambar ke RGB
    face_locations = face_recognition.face_locations(curPersonnRGB)  # Deteksi lokasi wajah

    # Periksa apakah gambar tidak memiliki wajah atau memiliki lebih dari satu wajah
    if not face_locations:
        print(f"Peringatan: Tidak ada wajah yang terdeteksi dalam gambar {cl}.")
        images_without_faces += 1
        continue
    elif len(face_locations) > 1:
        print(f"Peringatan: Lebih dari satu wajah terdeteksi dalam gambar {cl}.")
        images_with_multiple_faces += 1
        continue
    else:
        images.append(curPersonn)  # Tambahkan gambar ke list orang
        classNames.append(os.path.splitext(cl)[0])  # Tambahkan nama kelas ke list orang

# Jika ada gambar yang tidak memenuhi syarat, hentikan program
if images_without_faces > 0 or images_with_multiple_faces > 0:
    print("Program berhenti karena terdapat gambar yang tidak memenuhi syarat.\n")
    exit()

print(classNames)  # Cetak nama kelas yang valid

attendance_log = []  # Log untuk menyimpan catatan kehadiran


def findEncodeings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Konversi gambar ke RGB

        face_locations = face_recognition.face_locations(img)  # Deteksi lokasi wajah

        if len(face_locations) != 1:
            print(f"Peringatan: Gambar saat ini tidak memenuhi syarat (harus memiliki satu wajah). Program berhenti.")
            exit()

        encode = face_recognition.face_encodings(img, face_locations)[0]  # Dapatkan encoding wajah
        encodeList.append(encode)
    return encodeList

encodeListKnown = findEncodeings(images)  # Dapatkan encoding wajah yang dikenal
print("\nMemulai program...jika ingin keluar dan simpan perubahan, tekan 'Esc' pada keyboard atau klik icon keluar pada terminal\n")

cap = cv2.VideoCapture(0)  # Inisialisasi capture video dari webcam

# Muat suara notifikasi
terlambat_sound = pygame.mixer.Sound("notifikasi/terlambat1.mp3")
tidak_terlambat_sound = pygame.mixer.Sound("notifikasi/hadir1.mp3")
wajah_tidak_dikenali_sound = pygame.mixer.Sound("notifikasi/tidak_dikenali.mp3")

# Buat folder untuk menyimpan hasil absensi jika belum ada
folder_path = r'C:\Users\Chairil13\Documents\Hasil_absensi (tidak boleh diubah letak folder ini)'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

wajah_terdeteksi = False  # Flag untuk mendeteksi wajah

# Loop utama untuk memproses video frame per frame
while True:
    _, img = cap.read()  # Baca frame dari webcam
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Resize frame untuk mempercepat pemrosesan
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)  # Konversi frame ke RGB
    faceCurentFrame = face_recognition.face_locations(imgS)  # Deteksi lokasi wajah di frame saat ini
    encodeCurentFrame = face_recognition.face_encodings(imgS, faceCurentFrame)  # Dapatkan encoding wajah

    # Periksa setiap wajah yang terdeteksi dalam frame
    for faceLoc, encodeface in zip(faceCurentFrame, encodeCurentFrame):
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4  # Skala kembali koordinat wajah

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Gambar kotak di sekitar wajah

        matches = face_recognition.compare_faces(encodeListKnown, encodeface)  # Cocokkan wajah dengan wajah yang dikenal
        name = "Tidak dikenali"  # Default name jika wajah tidak dikenal

        # Jika wajah dikenal, dapatkan nama orang
        if True in matches:
            first_match_index = matches.index(True)
            name = classNames[first_match_index].title()

            # Coba muat gambar orang dari file JPG atau PNG
            person_image_path_jpg = os.path.join(path, f'{name.lower()}.jpg')
            person_image_path_png = os.path.join(path, f'{name.lower()}.png')

            if os.path.isfile(person_image_path_jpg):
                person_image = cv2.imread(person_image_path_jpg)
            elif os.path.isfile(person_image_path_png):
                person_image = cv2.imread(person_image_path_png)
            else:
                print(f"Peringatan: Gambar {name} tidak ditemukan.")
                continue

            # Tampilkan gambar kecil dari orang yang dikenal
            if person_image is not None:
                person_image = cv2.resize(person_image, (100, 100))
                img[0:100, 0:100] = person_image
                cv2.putText(img, name, (x1, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

                # Catat kehadiran jika orang belum tercatat
                if name not in [entry['name'] for entry in attendance_log]:
                    entry_time = datetime.now()
                    keterangan = 'Hadir'

                    # Tentukan keterangan berdasarkan waktu
                    if entry_time.time() > datetime.strptime('23:59', '%H:%M').time():
                        keterangan = 'Terlambat'
                        terlambat_sound.play()  # Putar suara terlambat
                    else:
                        tidak_terlambat_sound.play()  # Putar suara hadir

                    entry = {'name': name, 'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'), 'keterangan': keterangan}
                    attendance_log.append(entry)  # Tambahkan ke log kehadiran
        else:
            wajah_tidak_dikenali_sound.play()  # Putar suara wajah tidak dikenali
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img, "????????", (x1, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            print("Notifikasi: Wajah tidak dikenali terdeteksi!!!\n")

    # Tampilkan pesan di bagian bawah frame
    cv2.putText(img, "Tolong utamakan jujur dan masuk tepat waktu", (10, img.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imshow('Face Recognition', img)  # Tampilkan frame dengan kotak wajah dan informasi

    key = cv2.waitKey(1)  # Tunggu input keyboard selama 1 ms

    if key == 27:  # Jika tombol 'Esc' ditekan, simpan dan keluar
        for cl in personsList:
            name = os.path.splitext(cl)[0].title()

            # Tambahkan orang yang tidak hadir ke log kehadiran
            if name not in [entry['name'] for entry in attendance_log]:
                entry_time = datetime.now()
                keterangan = 'Tidak Hadir'

                entry = {'name': name, 'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'), 'keterangan': keterangan}
                attendance_log.append(entry)

        sorted_attendance = sorted(attendance_log, key=lambda x: x['name'])  # Urutkan log kehadiran

        # Simpan log kehadiran ke file Excel
        current_month = datetime.now().strftime("%m_%Y")
        file_name = f'Daftar_hadir_{current_month}.xlsx'
        file_path = os.path.join(folder_path, file_name)

        with pd.ExcelWriter(file_path, engine='xlsxwriter', datetime_format='yyyy-mm-dd hh:mm:ss') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet(datetime.now().strftime('%d_%m_%Y_%H%M%S'))

            # Format judul dan header
            judul_format = workbook.add_format(
                {'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
            bold_center_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            bold_format = workbook.add_format({'bold': True})

            worksheet.merge_range('A1:C1', 'Daftar Hadir - ' + datetime.now().strftime('%d %B %Y'), judul_format)

            worksheet.write(2, 0, 'Nama', bold_center_format)
            worksheet.write(2, 1, 'Waktu Absen', bold_center_format)
            worksheet.write(2, 2, 'Keterangan', bold_center_format)

            # Set lebar kolom berdasarkan panjang data maksimal
            max_length_nama = max([len(str(entry["name"])) for entry in sorted_attendance] + [len("Nama")])
            max_length_waktu_absen = max(
                [len(str(entry["entry_time"])) for entry in sorted_attendance] + [len("Waktu Absen")])
            max_length_keterangan = max(
                [len(str(entry["keterangan"])) for entry in sorted_attendance] + [len("Keterangan")])

            worksheet.set_column('A:A', max_length_nama + 1)
            worksheet.set_column('B:B', max_length_waktu_absen + 1)
            worksheet.set_column('C:C', max_length_keterangan + 1)

            # Tulis data kehadiran ke worksheet
            row = 3
            for entry in sorted_attendance:
                name = entry["name"]
                entry_time = entry["entry_time"]
                keterangan = entry["keterangan"]

                waktu_absen = '-' if keterangan == 'Tidak Hadir' else entry_time

                worksheet.write(row, 0, name)
                worksheet.write(row, 1, waktu_absen)
                worksheet.write(row, 2, keterangan)
                row += 1

            row += 1

            pegawai_set = set(entry['name'] for entry in sorted_attendance)
            total_pegawai = len(pegawai_set)

            worksheet.write(row, 0, 'Total Pegawai', bold_format)
            worksheet.write(row, 1, total_pegawai, bold_center_format)

            row += 2

            total_hadir = sum(entry['keterangan'] == 'Hadir' for entry in sorted_attendance)
            total_terlambat = sum(entry['keterangan'] == 'Terlambat' for entry in sorted_attendance)
            total_tidak_hadir = sum(entry['keterangan'] == 'Tidak Hadir' for entry in sorted_attendance)

            worksheet.write(row, 0, 'Total Hadir', bold_format)
            worksheet.write(row, 1, total_hadir, bold_center_format)

            worksheet.write(row + 1, 0, 'Total Terlambat', bold_format)
            worksheet.write(row + 1, 1, total_terlambat, bold_center_format)

            worksheet.write(row + 2, 0, 'Total Tidak Hadir', bold_format)
            worksheet.write(row + 2, 1, total_tidak_hadir, bold_center_format)

            # Buat diagram batang untuk visualisasi kehadiran
            categories = ['Total Hadir', 'Total Terlambat', 'Total Tidak Hadir']
            values = [total_hadir, total_terlambat, total_tidak_hadir]

            plt.bar(categories, values, color=['green', 'orange', 'red'])
            plt.xlabel('Kategori')
            plt.ylabel('Jumlah')
            plt.title('Diagram Kehadiran')

            current_month = datetime.now().strftime("%m_%Y")
            chart_image_filename = f'Daftar_hadir_{current_month} (Diagram).png'
            chart_image_path = os.path.join(folder_path, chart_image_filename)
            plt.savefig(chart_image_path)

            worksheet.insert_image('E10', chart_image_path, {'x_scale': 0.5, 'y_scale': 0.5})

        break  # Keluar dari loop utama
