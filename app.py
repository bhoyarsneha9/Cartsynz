import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from tracker import (
    load_alerts_for, add_alert, remove_alert, update_alert,
    check_cart_expiry, days_left_in_cart,
    get_price_with_tinyfish, get_product_info_with_tinyfish,
    add_to_cart_with_tinyfish, login_with_tinyfish,
    scrape_deals_with_tinyfish, load_deals, save_deals,
    get_user, upsert_user,
    generate_otp, verify_otp,
    send_sms_otp, send_sms_cart_alert,
    SITE_LOGIN_URLS,
)

# ─── ENV ──────────────────────────────────────────────────────────────────────
API_KEY       = os.getenv("TINYFISH_API_KEY", "")
TWILIO_SID    = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE  = os.getenv("TWILIO_PHONE", "")

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CARTSYNCZ",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { font-family: 'DM Sans', sans-serif; }

.stApp { background: #080810; color: #e8e8f0; }
.main .block-container { padding: 0 2rem 4rem 2rem; max-width: 1200px; }

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

h1, h2, h3, .brand { font-family: 'Syne', sans-serif; }

.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 0;
    border-bottom: 1px solid #1c1c2e;
    margin-bottom: 32px;
}
.brand-logo {
    font-family: 'Syne', sans-serif;
    font-size: 26px;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
}
.brand-tag {
    font-size: 11px;
    color: #555;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: -4px;
}
.nav-pills { display: flex; gap: 8px; }
.nav-pill {
    padding: 8px 18px;
    border-radius: 100px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid #1c1c2e;
    color: #888;
    background: transparent;
}
.nav-pill.active {
    background: linear-gradient(135deg, #a78bfa22, #60a5fa22);
    border-color: #a78bfa55;
    color: #c4b5fd;
}
.hero {
    text-align: center;
    padding: 50px 0 40px 0;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(40px, 7vw, 72px);
    font-weight: 800;
    line-height: 1.05;
    background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 16px;
}
.hero-sub {
    color: #666;
    font-size: 17px;
    max-width: 500px;
    margin: 0 auto 32px auto;
    line-height: 1.6;
}
.card {
    background: #0e0e1a;
    border: 1px solid #1c1c2e;
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
    transition: border-color 0.25s, transform 0.25s;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #a78bfa44, transparent);
}
.card:hover { border-color: #a78bfa44; transform: translateY(-2px); }
.card-deal {
    background: linear-gradient(135deg, #0e0e1a, #12101e);
    border: 1px solid #2a1a3e;
    border-radius: 20px;
    padding: 20px;
    transition: all 0.25s;
    height: 100%;
}
.card-deal:hover { border-color: #a78bfa66; transform: translateY(-3px); }
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 600;
}
.badge-site  { background: #1a2035; color: #60a5fa; border: 1px solid #1e3050; }
.badge-deal  { background: #1a2e1a; color: #4ade80; border: 1px solid #1e3e1e; }
.badge-cart  { background: #2e1a1a; color: #f87171; border: 1px solid #3e1e1e; }
.badge-hit   { background: #2a1a3e; color: #c4b5fd; border: 1px solid #3a2a5e; }
.price-current {
    font-family: 'Syne', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #c4b5fd;
    line-height: 1;
}
.price-range { font-size: 13px; color: #555; margin-top: 4px; }
.price-drop-pct {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: #4ade80;
}
.ticker-wrap {
    overflow: hidden;
    background: linear-gradient(90deg, #080810, #0e0e1a, #080810);
    border-top: 1px solid #1c1c2e;
    border-bottom: 1px solid #1c1c2e;
    padding: 10px 0;
    margin-bottom: 32px;
}
.ticker-inner {
    display: flex;
    gap: 60px;
    animation: ticker 30s linear infinite;
    white-space: nowrap;
    width: max-content;
}
@keyframes ticker {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
.ticker-item { font-size: 13px; color: #888; display: inline-flex; align-items: center; gap: 8px; }
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #e8e8f0;
    margin-bottom: 6px;
}
.section-sub { font-size: 14px; color: #555; margin-bottom: 24px; }
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] > div > div {
    background: #0e0e1a !important;
    border-color: #1c1c2e !important;
    color: #e8e8f0 !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    border: 1px solid #1c1c2e !important;
    background: #0e0e1a !important;
    color: #e8e8f0 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: #a78bfa55 !important;
    background: #12101e !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #3b82f6) !important;
    border-color: transparent !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px #7c3aed44 !important;
}
div[data-testid="stExpander"] {
    background: #0e0e1a !important;
    border: 1px solid #1c1c2e !important;
    border-radius: 16px !important;
}
.timer-bar-wrap {
    background: #1a1a2e;
    border-radius: 100px;
    height: 6px;
    margin-top: 8px;
    overflow: hidden;
}
.timer-bar {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, #f87171, #fbbf24);
}
.auth-wrap { max-width: 420px; margin: 60px auto; }
.auth-card {
    background: #0e0e1a;
    border: 1px solid #1c1c2e;
    border-radius: 24px;
    padding: 40px 36px;
}
.auth-title {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: #e8e8f0;
    margin-bottom: 8px;
    text-align: center;
}
.auth-sub { font-size: 14px; color: #555; text-align: center; margin-bottom: 28px; }
.deal-img {
    width: 100%;
    aspect-ratio: 1;
    border-radius: 12px;
    object-fit: cover;
}
.deal-img-placeholder {
    width: 100%;
    aspect-ratio: 1;
    border-radius: 12px;
    background: linear-gradient(135deg, #1a1a2e, #12101e);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
}
.vdivider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #1c1c2e, transparent);
    margin: 28px 0;
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #080810; }
::-webkit-scrollbar-thumb { background: #1c1c2e; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for key, default in {
    "page": "home",
    "auth_step": "phone",
    "auth_phone": "",
    "user": None,
    "site_sessions": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── API KEY CHECK ─────────────────────────────────────────────────────────────
if not API_KEY:
    st.error("⚠️ Add TINYFISH_API_KEY to your .env file and restart.")
    st.stop()

# ─── NAVBAR ───────────────────────────────────────────────────────────────────
pages = [
    ("🏠", "Home",    "home"),
    ("🎯", "Alerts",  "alerts"),
    ("🔥", "Deals",   "deals"),
    ("🛒", "Cart",    "cart"),
    ("⚙️", "Account", "account"),
]

nav_html = '<div class="navbar"><div><div class="brand-logo">CARTSYNCZ</div><div class="brand-tag">Smart Shopping Automation</div></div><div class="nav-pills">'
for icon, label, pid in pages:
    active = "active" if st.session_state.page == pid else ""
    nav_html += f'<div class="nav-pill {active}">{icon} {label}</div>'
nav_html += '</div></div>'
st.markdown(nav_html, unsafe_allow_html=True)

cols = st.columns(len(pages))
for i, (icon, label, pid) in enumerate(pages):
    with cols[i]:
        if st.button(f"{icon} {label}", key=f"nav_{pid}", use_container_width=True):
            st.session_state.page = pid
            st.rerun()

st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)


# ─── AUTH ─────────────────────────────────────────────────────────────────────
def render_auth():
    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="auth-card">
        <div class="auth-title">👋 Welcome to CARTSYNCZ</div>
        <div class="auth-sub">Sign in with your phone number to get started</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth_step == "phone":
        phone = st.text_input("Phone Number", placeholder="+91 98765 43210", key="input_phone")
        if st.button("Send OTP via SMS 📲", type="primary", use_container_width=True):
            phone = phone.strip().replace(" ", "")
            if not phone.startswith("+"):
                st.warning("Include country code e.g. +91...")
            else:
                otp = generate_otp(phone)
                if TWILIO_SID and TWILIO_TOKEN and TWILIO_PHONE:
                    ok = send_sms_otp(phone, otp, TWILIO_SID, TWILIO_TOKEN, TWILIO_PHONE)
                    if ok:
                        st.session_state.auth_phone = phone
                        st.session_state.auth_step = "otp"
                        st.success("✅ OTP sent via SMS!")
                        st.rerun()
                    else:
                        st.error("Could not send SMS. Check Twilio credentials in .env")
                else:
                    # Dev mode
                    st.session_state.auth_phone = phone
                    st.session_state.auth_step = "otp"
                    st.info(f"🔧 Dev mode — Your OTP is: **{otp}**")
                    st.rerun()

    elif st.session_state.auth_step == "otp":
        st.info(f"OTP sent to {st.session_state.auth_phone}")
        otp_input = st.text_input("Enter 6-digit OTP", max_chars=6, placeholder="123456", key="input_otp")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify OTP ✅", type="primary", use_container_width=True):
                if verify_otp(st.session_state.auth_phone, otp_input):
                    user = upsert_user(st.session_state.auth_phone, last_login=datetime.now().isoformat())
                    st.session_state.user = user
                    st.session_state.auth_step = "done"
                    st.success("Logged in! 🎉")
                    st.rerun()
                else:
                    st.error("Wrong or expired OTP. Try again.")
        with col2:
            if st.button("← Change Number", use_container_width=True):
                st.session_state.auth_step = "phone"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


protected = ["alerts", "cart", "account"]
if st.session_state.page in protected and not st.session_state.user:
    render_auth()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "home":

    st.markdown("""
    <div class="hero">
        <div class="hero-title">Shop Smarter.<br>Buy at the Right Price.</div>
        <div class="hero-sub">
            CARTSYNCZ watches prices across every shopping site.
            When your price drops — we add it to cart and send you an SMS.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    features = [
        ("🌐", "Any Website",    "Amazon, Flipkart, Myntra, Meesho, Nykaa and thousands more."),
        ("📱", "SMS Alerts",     "Instant SMS when your price target is hit and item is added."),
        ("🤖", "AI-Powered",     "TinyFish AI browses and shops for you automatically."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], features):
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center; padding:32px 24px;">
                <div style="font-size:36px; margin-bottom:12px;">{icon}</div>
                <div style="font-family:'Syne',sans-serif; font-size:17px; font-weight:700;
                            color:#e8e8f0; margin-bottom:8px;">{title}</div>
                <div style="font-size:14px; color:#555; line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)

    cola, colb = st.columns(2)
    with cola:
        if st.button("🎯 Set Price Alert", type="primary", use_container_width=True):
            st.session_state.page = "alerts"
            st.rerun()
    with colb:
        if st.button("🔥 Browse Deals", use_container_width=True):
            st.session_state.page = "deals"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ALERTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "alerts":

    phone = st.session_state.user["phone"]

    st.markdown('<div class="section-title">🎯 Add Price Alert</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Paste any product URL — from any shopping site.</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        new_url = st.text_input("Product URL", placeholder="https://amazon.in/dp/...  or  https://myntra.com/...", key="new_url")

        col_site, col_min, col_max = st.columns([2, 1, 1])
        with col_site:
            site_options = list(SITE_LOGIN_URLS.keys())
            new_site = st.selectbox("Shopping Site", site_options, key="new_site")
            if new_site == "Other":
                custom_site = st.text_input("Enter site name", placeholder="e.g. Croma", key="custom_site")
                if custom_site:
                    new_site = custom_site
        with col_min:
            min_price = st.number_input("Min Price (₹)", min_value=0.0, value=500.0, step=50.0, key="min_price")
        with col_max:
            max_price = st.number_input("Max Price (₹)", min_value=1.0, value=1500.0, step=50.0, key="max_price")

        st.markdown(f"""
        <div style="font-size:13px; color:#555; margin: 8px 0 16px 0;">
            Auto-add to cart when price is between
            <span style="color:#c4b5fd; font-weight:600;">₹{min_price:,.0f}</span> and
            <span style="color:#c4b5fd; font-weight:600;">₹{max_price:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Set Alert 🎯", type="primary", use_container_width=True):
            if not new_url.strip():
                st.warning("Please paste a product URL.")
            elif min_price >= max_price:
                st.warning("Max price must be greater than min price.")
            else:
                with st.spinner("Fetching product info via TinyFish AI…"):
                    info = get_product_info_with_tinyfish(new_url.strip(), API_KEY)
                alert = add_alert(phone, new_url.strip(), new_site, min_price, max_price)
                if info.get("price"):
                    update_alert(alert["id"],
                                 current_price=info["price"],
                                 product_name=info.get("name", ""),
                                 product_image=info.get("image", ""))
                st.success(f"✅ Alert set! Watching for ₹{min_price:,.0f} – ₹{max_price:,.0f}")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # Site Login
    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    with st.expander("🔐 Connect Shopping Accounts"):
        st.markdown('<div style="font-size:14px; color:#555; margin-bottom:16px;">Log in once — CARTSYNCZ auto-adds to cart when price drops.</div>', unsafe_allow_html=True)

        all_sites = [s for s in SITE_LOGIN_URLS.keys() if s != "Other"]
        l_site = st.selectbox("Select Site", all_sites, key="l_site")
        l_url  = SITE_LOGIN_URLS.get(l_site, "")
        if not l_url:
            l_url = st.text_input("Login page URL", key="l_custom_url")

        l_email = st.text_input("Email / Username", key="l_email")
        l_pass  = st.text_input("Password", type="password", key="l_pass")

        if st.button("Log In & Save Session 🔑", type="primary", use_container_width=True):
            if not l_email or not l_pass:
                st.warning("Enter your credentials.")
            else:
                with st.spinner(f"TinyFish AI logging into {l_site}… (30–90 sec)"):
                    ok, token, reason = login_with_tinyfish(l_site, l_email, l_pass, API_KEY, l_url)
                if ok:
                    st.session_state.site_sessions[l_site] = token
                    st.success(f"✅ Connected to {l_site}!")
                else:
                    st.error(f"❌ {reason}")

        if st.session_state.site_sessions:
            st.markdown("**Connected:**")
            for s in st.session_state.site_sessions:
                st.markdown(f'<span class="badge badge-site">✅ {s}</span>&nbsp;', unsafe_allow_html=True)

    # Alert Cards
    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    alerts = load_alerts_for(phone)

    for a in alerts:
        if check_cart_expiry(a):
            update_alert(a["id"], in_cart=False, cart_added_at=None)
    alerts = load_alerts_for(phone)

    if not alerts:
        st.markdown("""
        <div style="text-align:center; padding:60px 0; color:#333;">
            <div style="font-size:48px;">📭</div>
            <div style="font-size:16px; margin-top:12px;">No alerts yet. Add your first product above!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-title">📋 Your Alerts ({len(alerts)})</div>', unsafe_allow_html=True)

        for alert in reversed(alerts):
            aid     = alert["id"]
            min_p   = alert["min_price"]
            max_p   = alert["max_price"]
            current = alert.get("current_price")
            in_cart = alert.get("in_cart", False)
            site    = alert.get("site", "")
            url     = alert["url"]
            name    = alert.get("product_name", "") or url[:55] + "…"
            image   = alert.get("product_image", "")
            history = alert.get("price_history", [])

            price_in_range = current is not None and min_p <= current <= max_p
            short_url = url if len(url) <= 50 else url[:47] + "…"

            st.markdown('<div class="card">', unsafe_allow_html=True)
            col_img, col_info, col_act = st.columns([1, 3, 2])

            with col_img:
                if image:
                    st.markdown(f'<img src="{image}" class="deal-img"/>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="deal-img-placeholder">🛍️</div>', unsafe_allow_html=True)

            with col_info:
                st.markdown(f'<span class="badge badge-site">{site}</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:15px; font-weight:600; color:#e8e8f0; margin:8px 0 4px 0; line-height:1.4;">{name}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:12px; color:#333; margin-bottom:10px;"><a href="{url}" style="color:#555;">{short_url}</a></div>', unsafe_allow_html=True)

                if current:
                    price_color = "#4ade80" if price_in_range else "#c4b5fd"
                    st.markdown(f'<div class="price-current" style="color:{price_color};">₹{current:,.0f}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:#333; font-size:14px;">Price not checked yet</div>', unsafe_allow_html=True)

                st.markdown(f'<div class="price-range">Target range: ₹{min_p:,.0f} – ₹{max_p:,.0f}</div>', unsafe_allow_html=True)

                if price_in_range:
                    st.markdown('<span class="badge badge-hit">🎉 Price in range!</span>', unsafe_allow_html=True)

                if in_cart:
                    days = days_left_in_cart(alert)
                    pct  = (days / 7) * 100
                    st.markdown(f"""
                    <span class="badge badge-cart">🛒 In cart · {days}d left</span>
                    <div class="timer-bar-wrap"><div class="timer-bar" style="width:{pct}%;"></div></div>
                    """, unsafe_allow_html=True)

                if len(history) > 1:
                    import pandas as pd
                    df = pd.DataFrame(history)
                    df["at"] = pd.to_datetime(df["at"])
                    st.line_chart(df.set_index("at")["price"], height=60, use_container_width=True)

            with col_act:
                if st.button("🔍 Check Price", key=f"chk_{aid}", use_container_width=True):
                    with st.spinner("TinyFish AI checking price…"):
                        fetched = get_price_with_tinyfish(url, API_KEY)
                    if fetched is not None:
                        h = history + [{"price": fetched, "at": datetime.now().isoformat()}]
                        update_alert(aid, current_price=fetched, price_history=h)
                        st.success(f"₹{fetched:,.0f}")
                        st.rerun()
                    else:
                        st.error("Could not fetch price.")

                if price_in_range and not in_cart:
                    if st.button("🛒 Add to Cart", key=f"cart_{aid}", use_container_width=True, type="primary"):
                        sess = st.session_state.site_sessions.get(site, "")
                        if not sess:
                            st.warning(f"Connect your {site} account first ↑")
                        else:
                            with st.spinner("TinyFish AI adding to cart…"):
                                ok, reason = add_to_cart_with_tinyfish(url, site, API_KEY)
                            if ok:
                                update_alert(aid, in_cart=True, cart_added_at=datetime.now().isoformat())
                                if TWILIO_SID and TWILIO_TOKEN and TWILIO_PHONE:
                                    send_sms_cart_alert(
                                        phone, name, current, site,
                                        TWILIO_SID, TWILIO_TOKEN, TWILIO_PHONE
                                    )
                                st.success("✅ Added to cart! SMS alert sent.")
                                st.rerun()
                            else:
                                st.error(f"❌ {reason}")

                if st.button("🗑️ Remove", key=f"del_{aid}", use_container_width=True):
                    remove_alert(aid)
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DEALS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "deals":

    st.markdown('<div class="section-title">🔥 Top Price Drops Today</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Biggest discounts across popular shopping sites — powered by TinyFish AI</div>', unsafe_allow_html=True)

    ticker_items = [
        "Amazon 🔥 Up to 70% off Electronics",
        "Flipkart 🛒 Fashion sale live",
        "Myntra 👗 Min 50% off",
        "Meesho 💚 Prices drop every hour",
        "Nykaa 💄 Buy 2 Get 1 Free",
        "Ajio 👟 Sneakers at lowest ever",
    ]
    ticker_html = '<div class="ticker-wrap"><div class="ticker-inner">'
    for item in ticker_items * 2:
        ticker_html += f'<div class="ticker-item">🟢 {item}</div>'
    ticker_html += '</div></div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

    deal_sites = {
        "Amazon.in": "https://www.amazon.in/deals",
        "Flipkart":  "https://www.flipkart.com/offers-store",
        "Myntra":    "https://www.myntra.com/offers",
        "Meesho":    "https://www.meesho.com",
        "Nykaa":     "https://www.nykaa.com/offers",
    }

    selected_sites = st.multiselect(
        "Pick sites to scan for deals",
        list(deal_sites.keys()),
        default=["Amazon.in", "Flipkart"],
        key="deal_sites_select"
    )

    if st.button("🤖 Scan for Best Deals with TinyFish AI", type="primary", use_container_width=True):
        all_deals = []
        for site in selected_sites:
            with st.spinner(f"TinyFish AI scanning {site}…"):
                deals = scrape_deals_with_tinyfish(deal_sites[site], API_KEY, max_deals=4)
                for d in deals:
                    d["store"] = d.get("store") or site
                all_deals.extend(deals)
        save_deals(all_deals)
        st.rerun()

    deals = load_deals()

    if not deals:
        st.markdown("""
        <div style="text-align:center; padding:60px 0; color:#333;">
            <div style="font-size:48px;">🔍</div>
            <div style="font-size:16px; margin-top:12px;">Click the button above to scan for today's best deals!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        top = max(deals, key=lambda d: d.get("discount_pct") or 0)
        st.markdown(f"""
        <div class="card" style="background:linear-gradient(135deg,#12101e,#1a1030);
             border-color:#a78bfa33; padding:32px; margin-bottom:24px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                <span class="badge badge-deal">🏆 TOP DEAL</span>
                <span class="badge badge-site">{top.get('store','')}</span>
            </div>
            <div style="font-family:'Syne',sans-serif; font-size:22px; font-weight:700;
                        color:#e8e8f0; margin-bottom:12px; line-height:1.3;">
                {top.get('name','Product')}
            </div>
            <div style="display:flex; align-items:baseline; gap:16px;">
                <div class="price-drop-pct">↓ {top.get('discount_pct',0):.0f}% OFF</div>
                <div style="font-size:26px; color:#c4b5fd; font-weight:700;">₹{top.get('price',0):,.0f}</div>
                <div style="font-size:16px; color:#444; text-decoration:line-through;">₹{top.get('original_price',0):,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="margin-top:8px;">All Deals</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, deal in enumerate(deals):
            with cols[i % 3]:
                name  = deal.get("name", "Product")[:50]
                price = deal.get("price") or 0
                orig  = deal.get("original_price") or 0
                disc  = deal.get("discount_pct") or 0
                store = deal.get("store", "")
                img   = deal.get("image", "")
                durl  = deal.get("url", "#")

                st.markdown(f"""
                <div class="card-deal">
                    {'<img src="' + img + '" class="deal-img" style="margin-bottom:12px;"/>'
                     if img else
                     '<div class="deal-img-placeholder" style="margin-bottom:12px;">🛍️</div>'}
                    <span class="badge badge-site" style="margin-bottom:8px; display:inline-block;">{store}</span>
                    <div style="font-size:14px; font-weight:600; color:#c0c0d0;
                                line-height:1.4; margin-bottom:10px; min-height:40px;">{name}</div>
                    <div style="display:flex; align-items:baseline; gap:8px; flex-wrap:wrap;">
                        <span style="font-family:'Syne',sans-serif; font-size:20px;
                                     font-weight:700; color:#c4b5fd;">₹{price:,.0f}</span>
                        {f'<span style="font-size:13px;color:#444;text-decoration:line-through;">₹{orig:,.0f}</span>' if orig else ''}
                        {f'<span class="badge badge-deal" style="font-size:11px;">-{disc:.0f}%</span>' if disc else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🎯 Set Alert", key=f"deal_alert_{i}", use_container_width=True):
                    if st.session_state.user:
                        add_alert(st.session_state.user["phone"], durl, store, price * 0.9, price)
                        st.success("Alert set!")
                    else:
                        st.session_state.page = "alerts"
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CART
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "cart":
    phone  = st.session_state.user["phone"]
    alerts = [a for a in load_alerts_for(phone) if a.get("in_cart")]

    st.markdown('<div class="section-title">🛒 Items in Cart</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Items auto-added by CARTSYNCZ. They expire after 7 days.</div>', unsafe_allow_html=True)

    if not alerts:
        st.markdown("""
        <div style="text-align:center; padding:60px 0; color:#333;">
            <div style="font-size:48px;">🛒</div>
            <div style="font-size:16px; margin-top:12px;">Your cart is empty. Set alerts and let CARTSYNCZ fill it!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for a in alerts:
            days = days_left_in_cart(a)
            pct  = (days / 7) * 100 if days else 0
            name = a.get("product_name", "") or a["url"][:50]
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <span class="badge badge-site">{a.get('site','')}</span>
                        <div style="font-size:16px; font-weight:600; color:#e8e8f0; margin:8px 0 4px 0;">{name}</div>
                        <div class="price-current">₹{a.get('current_price',0):,.0f}</div>
                        <span class="badge badge-cart" style="margin-top:8px;">🛒 {days} days left</span>
                        <div class="timer-bar-wrap" style="width:200px; margin-top:8px;">
                            <div class="timer-bar" style="width:{pct}%;"></div>
                        </div>
                    </div>
                    <a href="{a['url']}" target="_blank"
                       style="font-size:13px; color:#a78bfa; text-decoration:none;">View ↗</a>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ACCOUNT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "account":
    user  = st.session_state.user
    phone = user["phone"]

    st.markdown('<div class="section-title">⚙️ Account</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="width:56px; height:56px; border-radius:50%;
                        background:linear-gradient(135deg,#7c3aed,#3b82f6);
                        display:flex; align-items:center; justify-content:center;
                        font-size:22px;">👤</div>
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:18px;
                            font-weight:700; color:#e8e8f0;">{phone}</div>
                <div style="font-size:13px; color:#555;">
                    Member since {user.get('created_at','')[:10]}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_alerts = load_alerts_for(phone)
    active  = [a for a in all_alerts if not a.get("in_cart")]
    in_cart = [a for a in all_alerts if a.get("in_cart")]

    c1, c2, c3 = st.columns(3)
    for col, label, val, icon in [
        (c1, "Active Alerts", len(active),     "🎯"),
        (c2, "In Cart",       len(in_cart),    "🛒"),
        (c3, "Total Tracked", len(all_alerts), "📊"),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:28px;">{icon}</div>
                <div style="font-family:'Syne',sans-serif; font-size:28px;
                            font-weight:800; color:#c4b5fd;">{val}</div>
                <div style="font-size:13px; color:#555;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔗 Connected Sites</div>', unsafe_allow_html=True)

    if st.session_state.site_sessions:
        for s in list(st.session_state.site_sessions.keys()):
            col_s, col_b = st.columns([3, 1])
            with col_s:
                st.markdown(f'<span class="badge badge-site">✅ {s}</span>', unsafe_allow_html=True)
            with col_b:
                if st.button("Disconnect", key=f"disc_{s}"):
                    del st.session_state.site_sessions[s]
                    st.rerun()
    else:
        st.markdown('<div style="color:#333; font-size:14px;">No sites connected yet.</div>', unsafe_allow_html=True)

    # SMS status
    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📱 SMS Alerts</div>', unsafe_allow_html=True)
    if TWILIO_SID and TWILIO_TOKEN and TWILIO_PHONE:
        st.markdown('<span class="badge badge-deal">✅ Twilio SMS Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-cart">⚠️ Twilio not configured — add to .env</span>', unsafe_allow_html=True)

    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.user = None
        st.session_state.auth_step = "phone"
        st.session_state.page = "home"
        st.rerun()

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:40px 0 10px 0; color:#222; font-size:12px;
            font-family:'DM Sans',sans-serif; letter-spacing:1px;">
    CARTSYNCZ · Powered by TinyFish AI 🐟 · Built for TinyFish Hackathon
</div>
""", unsafe_allow_html=True)
