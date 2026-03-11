# Elite Dance Academy 🎭

A full-stack Flask web app for Elite Dance Academy with Google OAuth, Supabase enrollment, and email notifications.

---

## 🚀 Deploy to Render (Step-by-Step)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/elite-dance.git
git push -u origin main
```

### 2. Create a Render Web Service
1. Go to [render.com](https://render.com) and sign in
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Name:** `elite-dance-academy`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
5. Click **Create Web Service**

### 3. Update Supabase Redirect URL
After deployment, go to your Supabase project:
- **Authentication → URL Configuration**
- Add your Render URL to **Redirect URLs**:
  ```
  https://your-app-name.onrender.com/
  ```
- Also update **Site URL** to your Render URL

### 4. Add Static Assets
Upload your images to the `static/` folder:
- `hero-dance.jpeg`
- `bharatanatyam.jpeg`
- `hiphop.jpeg`
- `kathak.png`
- `salsa.png`
- `contemporary.png`
- `ballet.png`
- `western.png`
- `kuchipudi.png`
- `freestyle.png`

---

## 📁 Project Structure
```
elite-dance/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── render.yaml         # Render config
├── templates/
│   └── index.html      # Frontend (mobile-optimized)
└── static/
    └── (your images)
```

---

## 📱 Mobile Features Added
- Hamburger menu for mobile navigation
- Bottom-sheet style modals on mobile
- `font-size: 16px` on inputs (prevents iOS zoom)
- `100svh` hero (respects mobile browser chrome)
- Touch-friendly tap targets (min 44px)
- Swipe-friendly scrollable modals
- Responsive 2-column dance grid on mobile
- `overflow-x: hidden` to prevent horizontal scroll
