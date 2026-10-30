## Context:
I want to revise the prototype website, before it is only simple. Now I want the prototype to be wider so it will include the interface of a staff (lets say his name is Adimas) that handles lets say 10 customers. And I also want a dashboard view for the staff so it can monitor his customer portfolio. Preserve current design for list page and customer detail page. For Dashboard page use BRI color palette with other colors that is relevant.

## Task:
1. Create Dummy Data
   Create 10 dummy data for customer-collateral Information data : 
   | Column Name | Data type | Data Sample | Desc |
   |-------------|-----------|-------------|-------|
   | Nama Debitur | String | Budi | Fill with common Indonesian name|
   | Jenis Kredit | String | Small | Fill with one of (Small, KPR) |
   | Oustanding | Integer | 800000000 | In rupiahs, fill with integer in range 800000000-4000000000 |
   | Unit Kerja | String | KC Bandung | Just fill with "KC Bandung" |
   | Status | String | NPL | Fill with SML 3 or NPL |
   | ID agunan | Integer | 1 | Number from 1-10 |
   | Jenis Agunan | String | Agunan Tanah Rumah Tinggal | Fill with one of these (Agunan Tanah Rumah Tinggal, Agunan Tanah, Agunan Properti Komersial |
   | Deskripsi Agunan | String | Rumah tinggal dengan luas tanah 568m² dan luas bangunan 160m². | Fill with the description of the collateral in Indonesian |
   | Alamat Agunan | String | Jl. Opik Gandamanah No.33, RT.3/RW.1, Munjuljaya, Kec. Purwakarta, Kabupaten Purwakarta, Jawa Barat 41117 | Fill with West Java, Indonesian address |
   | Luas Tanah | Integer | 500 | In square meter |
   | Luas Bangunan | Integer | 160 | In square meter (don't fill if it's Agunan Tanah) |
   | Jenis Sertifikat | String | Sertifikat Hak Milik | Just fill with Sertifikat Hak Milik |
   | Nomor Sertfikat | String | 09821980 | generate 8 random number |
   | Nilai Pasar Wajar | Integer | 1000000000 | In rupiahs, 1.4 * outstanding |
   | Nilai likuidasi | Integer | 850000000 | In rupiahs, 85% of Nilai Pasar Wajar |
   | CCR | Integer | 106.25% | In percentage, Nilai likuidasi/Outstanding |
   | Tanggal Penilaian Terakhir | Date | 6 Juli 2025 | Indonesian Date Format pick range from 2023-2026 |
   | Penilaian Agunan Terakhir Oleh | String | Bank | Just fill with either Bank or AO |
   | Nama perusahaan asuransi | String | ABD | Fill with Indonesian property insurance name |
   | Nilai coverage asuransi | Integer | 800000000 | Fill with suitable number for collateral insurance coverage |
3. List page
   Show All Nama Debitur, its outstanding, and status. Add filter by Jenis Kredit, Unit kerja, status, jenis agunan. Add search by Nama Debitur
4. Customer Detail page
   Will be opened by clicking data in list page
   - Customer & Collateral Information
     List down all the information of customer selected
   - Quadrant & Marketability Information
     User fill pop up questionnaire (questions and answer attached in xlsx, with Kategori to differentiate the section, show pertanyaan and jawaban (dont show the score)). Plez pre-fill 5 of the data (so there will be data in the dashboard). Sisanya user yang akan isi.
   - Add New Appraisal & Appraisal History
     Same as before (Riwayat Penilaian Agunan). Don't change anything
5. Dashboard Page
   Content:
   - Total Outstanding
   - Total Nilai Pasar Wajar
   - Total Nilai Likuidasi
   - CCR Outstanding terhadap Nilai Pasar dan terhadap Nilai Likuidasi
   - Kemutakhiran Penilaian (from last appraisal date)
   - Jenis Agunan distribution
   - Marketability & quadrant disribution
   Slicer:
   - Jenis Kredit
   - Unit kerja
   - Status

## Logic
- Marketability Logic
  So when user pick answer for each question, it has scores with range 1-5. Each category has the same weight so 4 categories, 1 category= 25%. Final score will be (total score from each categories * weight)/total category (4). EXCLUDE QUESTION L-3 & L-4 (it's for quadrant). If "Kuadran 4" even don't show the marketability, just show "Selesaikan masalah hukum agunan terlebih dahulu"
  | Overall score | Category |
  |---|---|
  | **4.00–5.00** | HIPO — High Potential |
  | **3.00–<4.00** | MEPO — Medium Potential |
  | **2.00–<3.00** | LOPO — Low Potential |
  | **1.00–<2.00** | NOPO — No Potential |
- Quadrant Logic
  if L-3 score = 5 THEN "Kuadran 1"
  else
    if L-4 score = 5 THEN "Kuadran 2"
      else (if L-4 score = 0) THEN "Kuadran 4"
   
