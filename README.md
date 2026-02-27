Kitty, you can has cheeeeeeseburger.
Roarrrrrrrrrrrr

狸，食堡。
善

ねこちゃん、チーズバーガー食べていいよぉぉぉ。
ガオオオオオオオ

고양이야, 치즈버거 먹어도 돼에에에.
어어어어흥——

Minou, tu peux avoir un chiiiiiiizburger.
Roooaaarrrrr

Kätzchen, du darfst einen Kääääääseburger haben.
Rooooaaarrrr

Котик, можешь съесть чииииизбургер.
Рррррррррр

---

## 本地运行与验证

**后端**（启动时 `init_db` 会自动创建 `users` 等表）：

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

**前端**：

```bash
cd frontend && npm install && npm run dev
```

浏览器访问前端地址（如 `http://localhost:5173`），未登录会跳转到 `/login`。先点「注册」完成注册，再登录即可进入首页；侧栏/导航有「设置」与「退出」。

**生产环境**：在 backend 配置 `JWT_SECRET` 环境变量，不要使用默认的 `change-me-in-production`。

**生产/演示地址**：https://cheeseburger-h272.onrender.com

**邀请制注册**：邀请链接由本地脚本生成并写入数据库，不通过 HTTP 接口。在 backend 目录执行：
`python scripts/generate_invites.py [--count 20] [--base-url https://cheeseburger-h272.onrender.com]`，需已配置 `DATABASE_URL`；可选在 `.env` 中设置 `INVITE_BASE_URL` 作为默认注册页 base。