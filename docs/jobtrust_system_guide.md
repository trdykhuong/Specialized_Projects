# JobTrust AI

## Muc tieu

Xay dung he thong quan ly va danh gia do tin cay tin tuyen dung ca nhan hoa ung dung Machine Learning.

## Kien truc

- `ml_pipeline/`: xu ly du lieu, gan nhan, train model ensemble.
- `flask_backend/`: API Flask phuc vu dashboard, danh gia tin, ca nhan hoa, blacklist.
- `frontend_react/`: giao dien ReactJS de demo de tai.

## Chuc nang chinh

- Dashboard tong quan ve phan bo muc rui ro.
- Quan ly danh sach tin tuyen dung da gan diem tin cay.
- Phan tich 1 tin tuyen dung moi bang model + heuristic.
- Ca nhan hoa goi y viec lam theo tu khoa va muc rui ro mong muon.
- Quan ly blacklist doanh nghiep, email, so dien thoai.

## Chay backend

```bash
cd flask_backend
pip install -r requirements.txt
python app.py
```

API mac dinh tai `http://localhost:5000/api`.

## Chay frontend

```bash
cd frontend_react
npm install
npm run dev
```

Frontend mac dinh tai `http://localhost:5173`.

## Luong demo bao ve de tai

1. Mo dashboard tong quan de trinh bay data va muc rui ro.
2. Vao `Quan ly tin` de xem kho du lieu va loc theo risk.
3. Vao `Danh gia tin cay` de nhap 1 tin moi va cham diem.
4. Vao `Ca nhan hoa` de goi y cong viec an toan cho ung vien.
5. Vao `Blacklist` de minh hoa co che canh bao bo sung.
