# Absensi berbasis Face Recognition

import cv2
import face_recognition
import os
from datetime import datetime
import pygame
import pandas as pd
import matplotlib.pyplot as plt

pygame.mixer.init()

path = 'orang'
images = []
classNames = []
images_without_faces = 0
images_with_multiple_faces = 0

personsList = os.listdir(path)

if not personsList:
    print("\nPeringatan: Folder 'orang' tidak berisi gambar, mohon input terlebih dahulu. Program berhenti.\n")
    exit()

for cl in personsList:
    curPersonn = cv2.imread(f'{path}/{cl}')

    curPersonnRGB = cv2.cvtColor(curPersonn, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(curPersonnRGB)

    if not face_locations:
        print(f"Peringatan: Tidak ada wajah yang terdeteksi dalam gambar {cl}.")
        images_without_faces += 1
        continue
    elif len(face_locations) > 1:
        print(f"Peringatan: Lebih dari satu wajah terdeteksi dalam gambar {cl}.")
        images_with_multiple_faces += 1
        continue
    else:
        images.append(curPersonn)
        classNames.append(os.path.splitext(cl)[0])

if images_without_faces > 0 or images_with_multiple_faces > 0:
    print("Program berhenti karena terdapat gambar yang tidak memenuhi syarat.\n")
    exit()

print(classNames)

attendance_log = []


def findEncodeings(image):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(img)

        if len(face_locations) != 1:
            print(f"Peringatan: Gambar saat ini tidak memenuhi syarat (harus memiliki satu wajah). Program berhenti.")
            exit()

        encode = face_recognition.face_encodings(img, face_locations)[0]
        encodeList.append(encode)
    return encodeList

encodeListKnown = findEncodeings(images)
print("\nMemulai program...jika ingin keluar dan simpan perubahan, tekan 'Esc' pada keyboard atau klik icon keluar pada terminal\n")

cap = cv2.VideoCapture(0)

terlambat_sound = pygame.mixer.Sound("notifikasi/terlambat1.mp3")
tidak_terlambat_sound = pygame.mixer.Sound("notifikasi/hadir1.mp3")
wajah_tidak_dikenali_sound = pygame.mixer.Sound("notifikasi/tidak_dikenali.mp3")

folder_path = r'C:\Users\Chairil13\Documents\Hasil_absensi (tidak boleh diubah letak folder ini)'

if not os.path.exists(folder_path):
    os.makedirs(folder_path)

wajah_terdeteksi = False

while True:
    _, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    faceCurentFrame = face_recognition.face_locations(imgS)
    encodeCurentFrame = face_recognition.face_encodings(imgS, faceCurentFrame)

    for faceLoc, encodeface in zip(faceCurentFrame, encodeCurentFrame):
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

        matches = face_recognition.compare_faces(encodeListKnown, encodeface)
        name = "Tidak dikenali"

        if True in matches:
            first_match_index = matches.index(True)
            name = classNames[first_match_index].title()

            person_image_path_jpg = os.path.join(path, f'{name.lower()}.jpg')
            person_image_path_png = os.path.join(path, f'{name.lower()}.png')

            if os.path.isfile(person_image_path_jpg):
                person_image = cv2.imread(person_image_path_jpg)
            elif os.path.isfile(person_image_path_png):
                person_image = cv2.imread(person_image_path_png)
            else:
                print(f"Peringatan: Gambar {name} tidak ditemukan.")
                continue

            if person_image is not None:
                person_image = cv2.resize(person_image, (100, 100))
                img[0:100, 0:100] = person_image
                cv2.putText(img, name, (x1, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

                if name not in [entry['name'] for entry in attendance_log]:
                    entry_time = datetime.now()
                    keterangan = 'Hadir'

                    if entry_time.time() > datetime.strptime('23:59', '%H:%M').time():
                        keterangan = 'Terlambat'
                        terlambat_sound.play()
                    else:
                        tidak_terlambat_sound.play()

                    entry = {'name': name, 'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'), 'keterangan': keterangan}
                    attendance_log.append(entry)
        else:
            wajah_tidak_dikenali_sound.play()
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img, "????????", (x1, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            print("Notifikasi: Wajah tidak dikenali terdeteksi!!!\n")

    cv2.putText(img, "Tolong utamakan jujur dan masuk tepat waktu", (10, img.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imshow('Face Recognition', img)

    key = cv2.waitKey(1)

    if key == 27:
        for cl in personsList:
            name = os.path.splitext(cl)[0].title()

            if name not in [entry['name'] for entry in attendance_log]:
                entry_time = datetime.now()
                keterangan = 'Tidak Hadir'

                entry = {'name': name, 'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'), 'keterangan': keterangan}
                attendance_log.append(entry)

        sorted_attendance = sorted(attendance_log, key=lambda x: x['name'])

        current_month = datetime.now().strftime("%m_%Y")
        file_name = f'Daftar_hadir_{current_month}.xlsx'
        file_path = os.path.join(folder_path, file_name)

        with pd.ExcelWriter(file_path, engine='xlsxwriter', datetime_format='yyyy-mm-dd hh:mm:ss') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet(datetime.now().strftime('%d_%m_%Y_%H%M%S'))

            judul_format = workbook.add_format(
                {'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
            bold_center_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            bold_format = workbook.add_format({'bold': True})

            worksheet.merge_range('A1:C1', 'Daftar Hadir - ' + datetime.now().strftime('%d %B %Y'), judul_format)

            worksheet.write(2, 0, 'Nama', bold_center_format)
            worksheet.write(2, 1, 'Waktu Absen', bold_center_format)
            worksheet.write(2, 2, 'Keterangan', bold_center_format)

            max_length_nama = max([len(str(entry["name"])) for entry in sorted_attendance] + [len("Nama")])
            max_length_waktu_absen = max(
                [len(str(entry["entry_time"])) for entry in sorted_attendance] + [len("Waktu Absen")])
            max_length_keterangan = max(
                [len(str(entry["keterangan"])) for entry in sorted_attendance] + [len("Keterangan")])

            worksheet.set_column('A:A', max_length_nama + 1)
            worksheet.set_column('B:B', max_length_waktu_absen + 1)
            worksheet.set_column('C:C', max_length_keterangan + 1)

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

        break
