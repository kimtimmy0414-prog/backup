<?php
session_start();
header('Content-Type: text/html; charset=utf-8');

$jsonFile = __DIR__ . '/data/users.json';
if (!file_exists(dirname($jsonFile))) mkdir(dirname($jsonFile), 0755, true);
if (!file_exists($jsonFile)) file_put_contents($jsonFile, '[]');

$users = json_decode(file_get_contents($jsonFile), true) ?: [];

function saveUsers() {
    global $jsonFile, $users;
    file_put_contents($jsonFile, json_encode($users, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);
}

function getUserIndex($username) {
    global $users;
    foreach ($users as $i => $u) if ($u['username'] === $username) return $i;
    return -1;
}

$action = $_GET['action'] ?? $_POST['action'] ?? 'home';
$msg = null;

$isAdmin = (isset($_SESSION['user']['username']) && $_SESSION['user']['username'] === 'Kim');

if ($action === 'register' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $u = trim($_POST['username'] ?? '');
    $p = $_POST['password'] ?? '';
    $pc = $_POST['password_confirm'] ?? '';
    $e = trim($_POST['email'] ?? '');

    if (empty($u) || $p !== $pc || strlen($p) < 8) {
        $msg = ['type'=>'danger', 'text'=>'입력 오류 또는 비밀번호 불일치'];
    } elseif (getUserIndex($u) !== -1) {
        $msg = ['type'=>'danger', 'text'=>'이미 존재하는 아이디'];
    } else {
        $users[] = [
            'username' => $u,
            'password' => password_hash($p, PASSWORD_DEFAULT),
            'email' => $e,
            'created_at' => date('Y-m-d H:i:s'),
            'active' => true,
            'balance' => 0,
            'deposit_count' => 0,
            'last_spin_date' => '',
            'total_deposit' => 0
        ];
        saveUsers();
        $msg = ['type'=>'success', 'text'=>'회원가입 완료! 로그인해주세요.'];
        header('Refresh:2; url=?action=login');
    }
}

if ($action === 'login' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $u = trim($_POST['username'] ?? '');
    $p = $_POST['password'] ?? '';
    $idx = getUserIndex($u);

    if ($idx !== -1 && password_verify($p, $users[$idx]['password'])) {
        $_SESSION['user'] = ['username' => $u, 'balance' => $users[$idx]['balance']];
        header('Location: ?action=home');
        exit;
    } else {
        $msg = ['type'=>'danger', 'text'=>'아이디/비밀번호 틀림'];
    }
}

if ($action === 'logout') {
    session_destroy();
    header('Location: ?action=login');
    exit;
}

if ($action === 'admin_charge' && $_SERVER['REQUEST_METHOD'] === 'POST' && $isAdmin) {
    $target = trim($_POST['target'] ?? '');
    $amount = intval($_POST['amount'] ?? 0);
    $idx = getUserIndex($target);
    if ($idx !== -1 && $amount > 0) {
        $users[$idx]['balance'] += $amount;
        $users[$idx]['deposit_count']++;
        $users[$idx]['total_deposit'] += $amount;
        saveUsers();
        $msg = ['type'=>'success', 'text'=> $target . '에게 ' . number_format($amount) . '원 충전 완료'];
    } else {
        $msg = ['type'=>'danger', 'text'=>'대상 유저 없음 또는 금액 오류'];
    }
}

if ($action === 'deposit' && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_SESSION['user'])) {
    $amount = intval($_POST['amount'] ?? 0);
    if ($amount >= 5000) {
        $msg = ['type'=>'success', 'text'=>"충전 신청 완료!\n계좌: 7777-03-0806539 (김시우)\n금액: ".number_format($amount)."원\n입금자명 확인 후 반영"];
    } else {
        $msg = ['type'=>'danger', 'text'=>'최소 5,000원 이상'];
    }
}

if ($action === 'spin' && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_SESSION['user'])) {
    $idx = getUserIndex($_SESSION['user']['username']);
    $user = &$users[$idx];
    $today = date('Y-m-d');

    if ($user['deposit_count'] == 0) {
        $msg = ['type'=>'danger', 'text'=>'충전 이력 필요'];
    } elseif ($user['last_spin_date'] === $today) {
        $msg = ['type'=>'danger', 'text'=>'오늘 이미 돌림'];
    } else {
        $prizes = [1000,1500,2000,2500,0,3000];
        $win = $prizes[array_rand($prizes)];
        $user['balance'] += $win;
        $user['last_spin_date'] = $today;
        saveUsers();
        $_SESSION['user']['balance'] = $user['balance'];
        $msg = ['type'=>'success', 'text'=> $win > 0 ? number_format($win).'원 당첨!' : '꽝!'];
    }
}

if ($action === 'play_crash' && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_SESSION['user'])) {
    $idx = getUserIndex($_SESSION['user']['username']);
    $bet = intval($_POST['bet'] ?? 0);
    if ($bet > 0 && $bet <= $users[$idx]['balance']) {
        $crash = max(1.0, round(1 / (mt_rand(1,1000000)/1000000 * 0.99 + 0.01), 2));
        $users[$idx]['balance'] -= $bet;
        saveUsers();
        $_SESSION['user']['balance'] = $users[$idx]['balance'];
        $msg = ['type'=>'info', 'text'=>"Crash Point: {$crash}×\n베팅 {$bet}원\n결과: 손실"];
    }
}

if ($action === 'play_baccarat' && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_SESSION['user'])) {
    $idx = getUserIndex($_SESSION['user']['username']);
    $bet = intval($_POST['bet'] ?? 0);
    $side = $_POST['side'] ?? 'player';

    if ($bet <= 0 || $bet > $users[$idx]['balance']) {
        $msg = ['type'=>'danger', 'text'=>'베팅 오류'];
    } else {
        function draw() { return mt_rand(1,13); }
        $p1 = draw(); $p2 = draw(); $player = ($p1 + $p2) % 10;
        $b1 = draw(); $b2 = draw(); $banker = ($b1 + $b2) % 10;

        $winner = $player > $banker ? 'player' : ($banker > $player ? 'banker' : 'tie');
        $payout = 0;
        if ($winner === $side) {
            if ($side === 'player') $payout = $bet * 2;
            if ($side === 'banker') $payout = $bet * 1.95;
            if ($side === 'tie') $payout = $bet * 9;
        }
        $users[$idx]['balance'] += $payout - $bet;
        saveUsers();
        $_SESSION['user']['balance'] = $users[$idx]['balance'];
        $msg = ['type'=>'info', 'text'=>"Player: $player | Banker: $banker\n승자: $winner\n지급: ".number_format($payout).'원'];
    }
}

?>
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>7bat - 대한민국 프리미엄 베팅 & 카지노</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {background:#0f0f1a;color:#ffd700;}
.card {background:#1a1a2e;border:1px solid #444;margin-bottom:1.5rem;}
h1,h2,h3,label,p,a,button {color:#ffd700;}
input.form-control,select {background:#2a2a3e;color:#ffd700;border:1px solid #555;}
.btn-primary {background:#ff2d55;color:#ffd700;font-weight:bold;}
.btn-success {background:#28a745;color:#ffd700;}
.btn-warning {background:#ffc107;color:#000;font-weight:bold;}
.hero {background:linear-gradient(rgba(0,0,0,0.7),rgba(0,0,0,0.7)),url('https://via.placeholder.com/1920x600/000/ffd700?text=7bat+Hero');background-size:cover;padding:100px 0;text-align:center;}
.roulette {width:280px;height:280px;border-radius:50%;border:15px solid #ffd700;position:relative;margin:20px auto;overflow:hidden;}
.roulette-inner {width:100%;height:100%;transition:transform 4s cubic-bezier(0.25,0.1,0.25,1);}
.segment {position:absolute;width:50%;height:50%;transform-origin:100% 100%;display:flex;align-items:center;justify-content:center;font-weight:bold;color:#000;font-size:14px;}
</style>
</head>
<body>

<?php if (isset($msg)): ?>
<div class="alert alert-<?=$msg['type']?> container"><?=nl2br(htmlspecialchars($msg['text']))?></div>
<?php endif; ?>

<?php if (!isset($_SESSION['user'])): ?>

<div class="hero">
<div class="container">
<h1 class="display-3 fw-bold">7bat과 함께 럭키 세븐 승리하세요!</h1>
<p class="lead">야구 특화 + 라이브 바카라 + 10,000+ 슬롯 | 첫 입금 500% 보너스</p>
<a href="?action=register" class="btn btn-primary btn-lg px-5 py-3">지금 가입하고 보너스 받기</a>
</div>
</div>

<div class="container py-5">
<div class="row justify-content-center">
<div class="col-md-8">
<div class="card p-4">
<h2 class="text-center mb-4">7bat 회사 소개</h2>
<p>2025년 설립된 대한민국 최적화 온라인 베팅 & 카지노 플랫폼입니다. Curaçao 라이선스 (No. 8048/JAZ) 아래 합법 운영 중이며, 한국어 풀 지원 + KRW 입출금 가능합니다.</p>
<h4>주요 서비스</h4>
<ul>
<li>스포츠 베팅 (야구 특화 + 35종 이상)</li>
<li>라이브 카지노 (바카라, 블랙잭, 룰렛 – Evolution 스타일)</li>
<li>슬롯 10,000+ </li>
<li>크래시 게임 (Aviator 스타일)</li>
<li>포커 & TV 게임</li>
</ul>
<h4>웰컴 보너스</h4>
<p class="fs-4 text-warning">첫 입금 500% (누적: 200% + 150% + 100% + 50%) 최대 ₩1,500,000</p>
<h4>입출금</h4>
<ul>
<li>은행 송금 / 카카오페이 스타일</li>
<li>USDT, BTC 등</li>
<li>최소 입금 ₩5,000 / 최소 출금 ₩10,000</li>
</ul>
<h4>고객지원</h4>
<p>24시간 한국어 라이브채팅 + 이메일</p>
<div class="text-center mt-4">
<a href="?action=register" class="btn btn-primary btn-lg">가입하고 500% 보너스 받기</a>
</div>
</div>
</div>
</div>
</div>

<?php else: ?>

<div class="container py-4">
<h1 class="text-center">7bat - 환영합니다, <?=htmlspecialchars($_SESSION['user']['username'])?>님</h1>
<p class="text-center fs-4">잔액: <?=number_format($_SESSION['user']['balance'])?>원</p>

<?php if ($isAdmin): ?>
<div class="card p-4 mb-4">
<h3>관리자 패널 - 직접 충전</h3>
<form method="post">
<input type="hidden" name="action" value="admin_charge">
<div class="mb-3"><label>대상 아이디</label><input type="text" name="target" class="form-control" required></div>
<div class="mb-3"><label>충전 금액</label><input type="number" name="amount" class="form-control" required></div>
<button type="submit" class="btn btn-danger w-100">충전 실행</button>
</form>
</div>
<?php endif; ?>

<div class="row">
<div class="col-md-4">
<div class="card p-4">
<h3>충전</h3>
<form method="post">
<input type="hidden" name="action" value="deposit">
<div class="mb-3"><input type="number" name="amount" class="form-control" min="5000" placeholder="5000 이상" required></div>
<button type="submit" class="btn btn-success w-100">충전 신청</button>
</form>
<p class="small mt-3 text-center">카카오뱅크 7777-03-0806539 김시우</p>
</div>
</div>

<div class="col-md-4">
<div class="card p-4 text-center">
<h3>매일 프리스핀</h3>
<div id="roulette" class="roulette mx-auto">
<div id="wheel" class="roulette-inner">
<div class="segment" style="background:#ff2d55;transform:rotate(0deg);">1000</div>
<div class="segment" style="background:#ffd700;transform:rotate(60deg);">1500</div>
<div class="segment" style="background:#28a745;transform:rotate(120deg);">2000</div>
<div class="segment" style="background:#007bff;transform:rotate(180deg);">2500</div>
<div class="segment" style="background:#ff2d55;transform:rotate(240deg);">꽝</div>
<div class="segment" style="background:#ffd700;transform:rotate(300deg);">3000</div>
</div>
</div>
<form method="post" id="spinForm">
<input type="hidden" name="action" value="spin">
<button type="submit" class="btn btn-warning w-100 mt-3" onclick="spinRoulette(event)">프리스핀 돌리기</button>
</form>
</div>
</div>

<div class="col-md-4">
<div class="card p-4">
<h3>게임 카테고리</h3>
<div class="d-grid gap-2">
<a href="?action=crash" class="btn btn-danger">Crash 게임</a>
<a href="?action=baccarat" class="btn btn-primary">라이브 바카라</a>
</div>
</div>
</div>
</div>

<?php if ($action === 'crash'): ?>
<div class="card p-4 mt-4">
<h3>Crash 게임</h3>
<form method="post">
<input type="hidden" name="action" value="play_crash">
<div class="mb-3"><input type="number" name="bet" class="form-control" value="1000" required placeholder="베팅액"></div>
<button type="submit" class="btn btn-danger w-100">베팅 시작</button>
</form>
</div>
<?php endif; ?>

<?php if ($action === 'baccarat'): ?>
<div class="card p-4 mt-4">
<h3>라이브 바카라</h3>
<form method="post">
<input type="hidden" name="action" value="play_baccarat">
<div class="mb-3"><input type="number" name="bet" class="form-control" value="1000" required placeholder="베팅액"></div>
<select name="side" class="form-select">
<option value="player">Player</option>
<option value="banker">Banker</option>
<option value="tie">Tie</option>
</select>
<button type="submit" class="btn btn-primary w-100 mt-3">베팅</button>
</form>
</div>
<?php endif; ?>

<div class="text-center mt-5">
<a href="?action=logout" class="btn btn-outline-danger">로그아웃</a>
</div>

<?php endif; ?>

<script>
function spinRoulette(e) {
    e.preventDefault();
    const wheel = document.getElementById('wheel');
    const deg = 1800 + Math.floor(Math.random() * 360);
    wheel.style.transform = `rotate(${deg}deg)`;
    setTimeout(() => document.getElementById('spinForm').submit(), 4200);
}
</script>
</body>
</html>
