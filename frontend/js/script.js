 const API_URL = 'https://ctrl-hora-backend.onrender.com';
        let token = null;

        // Login
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            try {
                const res = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `username=${username}&password=${password}`
                });
                if (!res.ok) throw new Error('Login failed');
                const data = await res.json();
                token = data.access_token;
                document.getElementById('controls').style.display = 'block';
                document.getElementById('loginForm').style.display = 'none';
                showMessage('Login exitoso');

                // Check if user is admin
                checkAdminStatus();

            } catch (err) {
                showMessage('Error: ' + err.message);
            }
        });

        async function checkAdminStatus() {
            try {
                const res = await fetch(`${API_URL}/api/users`, {
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    document.getElementById('adminPanel').style.display = 'block';
                    fetchUsers();
                }
            } catch (err) {
                // User is not an admin, so API call fails with 403
                console.log("No eres administrador, panel de admin no visible.");
            }
        }

        // Get GPS
        async function getGPS() {
            return new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(pos => {
                    resolve(`${pos.coords.latitude},${pos.coords.longitude}`);
                }, reject);
            });
        }

        // Entry
        document.getElementById('entryBtn').addEventListener('click', async () => {
            try {
                const gps = await getGPS();
                const res = await fetch(`${API_URL}/entry?gps_position=${gps}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Entry failed');
                showMessage('Ingreso registrado');
            } catch (err) {
                showMessage('Error: ' + err.message);
            }
        });

        // Exit
        document.getElementById('exitBtn').addEventListener('click', async () => {
            try {
                const gps = await getGPS();
                const res = await fetch(`${API_URL}/exit?gps_position=${gps}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Exit failed');
                showMessage('Salida registrada');
            } catch (err) {
                showMessage('Error: ' + err.message);
            }
        });

        function showMessage(msg) {
            document.getElementById('message').textContent = msg;
        }

        // ADMIN PANEL LOGIC

        async function fetchUsers() {
            try {
                const res = await fetch(`${API_URL}/api/users`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Failed to fetch users');
                const users = await res.json();
                const userList = document.getElementById('userList');
                userList.innerHTML = '';
                users.forEach(user => {
                    const li = document.createElement('li');
                    li.textContent = `User: ${user.username}, Admin: ${user.is_admin}`;
                    userList.appendChild(li);
                });
            } catch (err) {
                showMessage('Error al cargar la lista de usuarios');
            }
        }

        document.getElementById('createUserForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const newUsername = document.getElementById('newUsername').value;
            const newPassword = document.getElementById('newPassword').value;
            const isAdmin = document.getElementById('isAdminCheckbox').checked;

            try {
                const res = await fetch(`${API_URL}/api/users`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ username: newUsername, password: newPassword, is_admin: isAdmin })
                });
                if (!res.ok) throw new Error('Failed to create user');
                showMessage('Usuario creado exitosamente');
                document.getElementById('createUserForm').reset();
                fetchUsers();
            } catch (err) {
                showMessage('Error: ' + err.message);
            }
        });
document.getElementById('logoutBtn').addEventListener('click', () => {
    token = null;
    document.getElementById('controls').style.display = 'none';
    document.getElementById('adminPanel').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
    showMessage('Logout exitoso');
});