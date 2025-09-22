import { useState, useEffect } from 'react';

function App() {
  const [users, setUsers] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('adminToken') || '');
  const [newUser, setNewUser] = useState({ username: '', password: '', is_admin: false });
  const [editUser, setEditUser] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (token) {
      fetchUsers();
    }
  }, [token]);

  const fetchUsers = async () => {
    try {
      const res = await fetch('https://ctrl-hora-backend.onrender.com/api/users', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Unauthorized');
      const data = await res.json();
      setUsers(data);
    } catch (err) {
      setMessage('Error fetching users or unauthorized');
      setUsers([]);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;
    try {
      const res = await fetch('https://ctrl-hora-backend.onrender.com/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${username}&password=${password}`,
      });
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      const adminToken = data.access_token;
      setToken(adminToken);
      localStorage.setItem('adminToken', adminToken);
      setMessage('Login successful');
      fetchUsers();
    } catch (err) {
      setMessage('Invalid credentials');
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('https://ctrl-hora-backend.onrender.com/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(newUser),
      });
      if (!res.ok) throw new Error('Failed to create user');
      setMessage('User created successfully');
      setNewUser({ username: '', password: '', is_admin: false });
      fetchUsers();
    } catch (err) {
      setMessage(err.message);
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    if (!editUser) return;
    try {
      const res = await fetch(`https://ctrl-hora-backend.onrender.com/api/users/${editUser.username}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(editUser),
      });
      if (!res.ok) throw new Error('Failed to update user');
      setMessage('User updated successfully');
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      setMessage(err.message);
    }
  };

  const handleDeleteUser = async (username) => {
    if (window.confirm(`Are you sure you want to delete ${username}?`)) {
      try {
        const res = await fetch(`https://ctrl-hora-backend.onrender.com/api/users/${username}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!res.ok) throw new Error('Failed to delete user');
        setMessage('User deleted successfully');
        fetchUsers();
      } catch (err) {
        setMessage(err.message);
      }
    }
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('adminToken');
    setUsers([]);
    setMessage('Logged out');
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <form onSubmit={handleLogin} className="bg-white p-6 rounded shadow-md">
          <h2 className="text-2xl mb-4">Admin Login</h2>
          <input
            type="text"
            name="username"
            placeholder="Username"
            className="border p-2 mb-2 w-full"
            required
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            className="border p-2 mb-2 w-full"
            required
          />
          <button type="submit" className="bg-blue-500 text-white p-2 w-full">Login</button>
          {message && <p className="mt-2 text-red-500">{message}</p>}
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="bg-white p-6 rounded shadow-md">
        <h2 className="text-2xl mb-4">User Administration</h2>
        <button onClick={handleLogout} className="bg-red-500 text-white p-2 mb-4">Logout</button>
        <h3 className="text-xl mb-2">Create User</h3>
        <form onSubmit={handleCreateUser} className="mb-4">
          <input
            type="text"
            value={newUser.username}
            onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
            placeholder="Username"
            className="border p-2 mb-2 w-full"
            required
          />
          <input
            type="password"
            value={newUser.password}
            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
            placeholder="Password"
            className="border p-2 mb-2 w-full"
            required
          />
          <label className="block mb-2">
            <input
              type="checkbox"
              checked={newUser.is_admin}
              onChange={(e) => setNewUser({ ...newUser, is_admin: e.target.checked })}
            /> Is Admin
          </label>
          <button type="submit" className="bg-green-500 text-white p-2">Create</button>
        </form>
        {message && <p className="mb-4 text-red-500">{message}</p>}
        <h3 className="text-xl mb-2">Users</h3>
        <ul className="list-disc pl-5">
          {users.map((user) => (
            <li key={user._id} className="mb-2">
              {user.username} (Admin: {user.is_admin ? 'Yes' : 'No'})
              <button
                onClick={() => setEditUser({ username: user.username, password: '', is_admin: user.is_admin })}
                className="bg-yellow-500 text-white p-1 ml-2"
              >
                Edit
              </button>
              <button
                onClick={() => handleDeleteUser(user.username)}
                className="bg-red-500 text-white p-1 ml-2"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
        {editUser && (
          <form onSubmit={handleUpdateUser} className="mt-4">
            <input
              type="text"
              value={editUser.username}
              onChange={(e) => setEditUser({ ...editUser, username: e.target.value })}
              className="border p-2 mb-2 w-full"
              required
              disabled
            />
            <input
              type="password"
              value={editUser.password}
              onChange={(e) => setEditUser({ ...editUser, password: e.target.value })}
              placeholder="New Password"
              className="border p-2 mb-2 w-full"
            />
            <label className="block mb-2">
              <input
                type="checkbox"
                checked={editUser.is_admin}
                onChange={(e) => setEditUser({ ...editUser, is_admin: e.target.checked })}
              /> Is Admin
            </label>
            <button type="submit" className="bg-blue-500 text-white p-2">Update</button>
            <button onClick={() => setEditUser(null)} className="bg-gray-500 text-white p-2 ml-2">Cancel</button>
          </form>
        )}
      </div>
    </div>
  );
}

export default App;