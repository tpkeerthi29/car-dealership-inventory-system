
import { useEffect, useState } from 'react'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState(
    () => localStorage.getItem('access_token') || '',
  )
  const [userRole, setUserRole] = useState(
    () => localStorage.getItem('user_role') || '',
  )
  const [loginType, setLoginType] = useState('user')
  const [vehicles, setVehicles] = useState([])
  const [search, setSearch] = useState('')
  const [inventoryLoading, setInventoryLoading] = useState(false)

  const [showAddForm, setShowAddForm] = useState(false)
  const [newVehicle, setNewVehicle] = useState({
    make: '',
    model: '',
    category: '',
    price: '',
    quantity: '',
  })

  async function handleSubmit(event) {
    event.preventDefault()
    setMessage('')
    setLoading(true)

    try {
      if (isRegister) {
        const response = await fetch(`${API_URL}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        })
        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Registration failed')
        }

        setMessage('Registration successful! You can now sign in.')
        setIsRegister(false)
        setPassword('')
      } else {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)

        const response = await fetch(`${API_URL}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: formData,
        })
        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Login failed')
        }

        localStorage.setItem('access_token', data.access_token)
        setToken(data.access_token)

        const payload = JSON.parse(atob(data.access_token.split('.')[1]))
        const role = payload.role

        if (role !== 'admin' && role !== 'user') {
          localStorage.removeItem('access_token')
          setToken('')
          throw new Error('Invalid user role.')
        }

        if (role !== loginType) {
          localStorage.removeItem('access_token')
          setToken('')
          throw new Error(
            `This account is not authorized for ${loginType === 'admin' ? 'Admin' : 'User'} Login.`,
          )
        }

        localStorage.setItem('user_role', role)
        setUserRole(role)
        setMessage('')
      }
    } catch (error) {
      setMessage(error.message || 'Unable to connect to the server.')
    } finally {
      setLoading(false)
    }
  }

  async function loadVehicles(currentToken = token, query = search) {
    setInventoryLoading(true)
    setMessage('')

    try {
      const params = new URLSearchParams()
      if (query.trim()) {
        params.set('make', query.trim())
        params.set('model', query.trim())
        params.set('category', query.trim())
      }

      // Search across the supported fields using separate requests.
      const headers = { Authorization: `Bearer ${currentToken}` }
      let results

      if (query.trim()) {
        const searches = await Promise.all(
          ['make', 'model', 'category'].map(async (field) => {
            const response = await fetch(
              `${API_URL}/api/vehicles?${field}=${encodeURIComponent(query.trim())}`,
              { headers },
            )
            if (response.status === 401) {
              throw new Error('Your session has expired. Please sign in again.')
            }
            if (!response.ok) throw new Error('Could not load vehicles.')
            return response.json()
          }),
        )
        results = searches.flat()
        results = results.filter(
          (vehicle, index, array) =>
            array.findIndex((item) => item.id === vehicle.id) === index,
        )
      } else {
        const response = await fetch(`${API_URL}/api/vehicles`, { headers })
        if (response.status === 401) {
          throw new Error('Your session has expired. Please sign in again.')
        }
        if (!response.ok) throw new Error('Could not load vehicles.')
        results = await response.json()
      }

      setVehicles(results)
    } catch (error) {
      setMessage(error.message || 'Unable to load inventory.')
      if (error.message.includes('session has expired')) logout()
    } finally {
      setInventoryLoading(false)
    }
  }

  useEffect(() => {
    if (token) loadVehicles(token, '')
  }, [token])

 
function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_role')
  setToken('')
  setUserRole('')
  setVehicles([])
  setUsername('')
  setPassword('')
  setMessage('')
}



  async function handleAddVehicle(event) {
    event.preventDefault()
    setMessage('')

    try {
      const response = await fetch(`${API_URL}/api/vehicles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          make: newVehicle.make.trim(),
          model: newVehicle.model.trim(),
          category: newVehicle.category.trim(),
          price: Number(newVehicle.price),
          quantity: Number(newVehicle.quantity),
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Could not add vehicle')
      }

      setNewVehicle({
        make: '',
        model: '',
        category: '',
        price: '',
        quantity: '',
      })
      setShowAddForm(false)
      setMessage('Vehicle added successfully!')
      await loadVehicles(token, '')
      setSearch('')
    } catch (error) {
      setMessage(error.message || 'Unable to add vehicle')
    }
  }


  async function handlePurchase(vehicleId) {
    const quantity = Number(
      window.prompt('How many units would you like to purchase?', '1'),
    )

    if (!Number.isInteger(quantity) || quantity <= 0) {
      setMessage('Please enter a valid positive quantity.')
      return
    }

    try {
      setMessage('')

      const response = await fetch(
        `${API_URL}/api/vehicles/${vehicleId}/purchase`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ quantity }),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Purchase failed.')
      }

      setMessage('Purchase successful!')
      await loadVehicles(token, search)
    } catch (error) {
      setMessage(error.message || 'Unable to complete purchase.')
    }
  }


  async function handleRestock(vehicleId) {
    const quantity = Number(
      window.prompt('How many units would you like to add to stock?', '5'),
    )

    if (!Number.isInteger(quantity) || quantity <= 0) {
      setMessage('Please enter a valid positive quantity.')
      return
    }

    try {
      setMessage('')

      const response = await fetch(
        `${API_URL}/api/vehicles/${vehicleId}/restock`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ quantity }),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Restocking failed.')
      }

      setMessage('Vehicle restocked successfully!')
      await loadVehicles(token, search)
    } catch (error) {
      setMessage(error.message || 'Unable to restock vehicle.')
    }
  }

  async function handleEditVehicle(vehicle) {
    const make = window.prompt('Vehicle make:', vehicle.make)
    if (make === null) return

    const model = window.prompt('Vehicle model:', vehicle.model)
    if (model === null) return

    const category = window.prompt('Vehicle category:', vehicle.category)
    if (category === null) return

    const priceInput = window.prompt('Vehicle price:', String(vehicle.price))
    if (priceInput === null) return

    const quantityInput = window.prompt(
      'Available quantity:',
      String(vehicle.quantity),
    )
    if (quantityInput === null) return

    const price = Number(priceInput)
    const quantity = Number(quantityInput)

    if (
      !make.trim() ||
      !model.trim() ||
      !category.trim() ||
      !Number.isFinite(price) ||
      price <= 0 ||
      !Number.isInteger(quantity) ||
      quantity < 0
    ) {
      setMessage('Enter valid vehicle details. Price must be positive and quantity cannot be negative.')
      return
    }

    try {
      setMessage('')

      const response = await fetch(
        `${API_URL}/api/vehicles/${vehicle.id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            make: make.trim(),
            model: model.trim(),
            category: category.trim(),
            price,
            quantity,
          }),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to update vehicle.')
      }

      setMessage('Vehicle updated successfully!')
      await loadVehicles(token, search)
    } catch (error) {
      setMessage(error.message || 'Unable to update vehicle.')
    }
  }

  async function handleDeleteVehicle(vehicle) {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${vehicle.make} ${vehicle.model}?`,
    )

    if (!confirmed) return

    try {
      setMessage('')

      const response = await fetch(
        `${API_URL}/api/vehicles/${vehicle.id}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      )

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Unable to delete vehicle.')
      }

      setMessage('Vehicle deleted successfully!')
      await loadVehicles(token, search)
    } catch (error) {
      setMessage(error.message || 'Unable to delete vehicle.')
    }
  }


  if (token) {
    return (
      <div className="min-h-screen bg-slate-100">
        <header className="bg-slate-900 text-white">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5">
            <div>
              <p className="text-sm font-semibold uppercase tracking-widest text-blue-300">
                Dealership Management
              </p>
              <h1 className="mt-1 text-2xl font-bold">
                Vehicle Inventory
              </h1>
            </div>
            <button
              onClick={logout}
              className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-semibold hover:bg-slate-800"
            >
              Sign out
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-8">
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Vehicle models listed</p>
              <p className="mt-2 text-3xl font-bold text-slate-900">
                {vehicles.length}
              </p>
            </div>
            <div className="rounded-xl bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Units in stock</p>
              <p className="mt-2 text-3xl font-bold text-slate-900">
                {vehicles.reduce((total, vehicle) => total + vehicle.quantity, 0)}
              </p>
            </div>
            <div className="rounded-xl bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Inventory status</p>
              <p className="mt-2 text-lg font-bold text-emerald-700">
                Connected
              </p>
            </div>
          </div>

          <section className="rounded-xl bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  Available vehicles
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Search by make, model, or category.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {userRole === 'admin' && (
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
                >
                  {showAddForm ? 'Cancel' : 'Add vehicle'}
                </button>
                )}

                <button
                  onClick={() => loadVehicles(token, search)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50"
                >
                  Refresh
                </button>
              </div>

            </div>

            {userRole === 'admin' && showAddForm && (
              <form
                onSubmit={handleAddVehicle}
                className="mt-6 grid gap-4 rounded-xl border border-slate-200 bg-slate-50 p-5 sm:grid-cols-2 lg:grid-cols-3"
              >
                <h3 className="text-lg font-semibold text-slate-900 sm:col-span-2 lg:col-span-3">
                  Add a vehicle
                </h3>

                <input
                  required
                  placeholder="Make (e.g. Toyota)"
                  value={newVehicle.make}
                  onChange={(event) =>
                    setNewVehicle({ ...newVehicle, make: event.target.value })
                  }
                  className="rounded-lg border border-slate-300 bg-white px-3 py-3"
                />

                <input
                  required
                  placeholder="Model (e.g. Camry)"
                  value={newVehicle.model}
                  onChange={(event) =>
                    setNewVehicle({ ...newVehicle, model: event.target.value })
                  }
                  className="rounded-lg border border-slate-300 bg-white px-3 py-3"
                />

                <input
                  required
                  placeholder="Category (e.g. Sedan)"
                  value={newVehicle.category}
                  onChange={(event) =>
                    setNewVehicle({ ...newVehicle, category: event.target.value })
                  }
                  className="rounded-lg border border-slate-300 bg-white px-3 py-3"
                />

                <input
                  required
                  type="number"
                  min="0.01"
                  step="0.01"
                  placeholder="Price (₹)"
                  value={newVehicle.price}
                  onChange={(event) =>
                    setNewVehicle({ ...newVehicle, price: event.target.value })
                  }
                  className="rounded-lg border border-slate-300 bg-white px-3 py-3"
                />

                <input
                  required
                  type="number"
                  min="0"
                  step="1"
                  placeholder="Quantity"
                  value={newVehicle.quantity}
                  onChange={(event) =>
                    setNewVehicle({ ...newVehicle, quantity: event.target.value })
                  }
                  className="rounded-lg border border-slate-300 bg-white px-3 py-3"
                />

                <button
                  type="submit"
                  className="rounded-lg bg-emerald-700 px-4 py-3 font-semibold text-white hover:bg-emerald-800"
                >
                  Save vehicle
                </button>
              </form>
            )}

            <form
              className="mt-5 flex flex-col gap-3 sm:flex-row"
              onSubmit={(event) => {
                event.preventDefault()
                loadVehicles(token, search)
              }}
            >
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="e.g. Toyota, Camry, Sedan"
                className="min-w-0 flex-1 rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              />
              <button
                type="submit"
                className="rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white hover:bg-blue-800"
              >
                Search
              </button>
              <button
                type="button"
                onClick={() => {
                  setSearch('')
                  loadVehicles(token, '')
                }}
                className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700 hover:bg-slate-50"
              >
                Clear
              </button>
            </form>

            {message && (
              <p role="status" className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
                {message}
              </p>
            )}

            {inventoryLoading ? (
              <p className="py-10 text-center text-slate-500">Loading inventory...</p>
            ) : vehicles.length === 0 ? (
              <div className="py-12 text-center">
                <p className="font-semibold text-slate-700">No vehicles found</p>
                <p className="mt-2 text-sm text-slate-500">
                  Your inventory may be empty, or your search returned no matches.
                </p>
              </div>
            ) : (
              <div className="mt-6 overflow-x-auto">
                <table className="w-full min-w-[600px] text-left text-sm">
                  <thead className="bg-slate-50 text-slate-600">
                    <tr>
                      <th className="px-4 py-3">Make</th>
                      <th className="px-4 py-3">Model</th>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Price</th>
                      <th className="px-4 py-3">Quantity</th>
                      <th className="px-4 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {vehicles.map((vehicle) => (
                      <tr key={vehicle.id} className="hover:bg-slate-50">
                        <td className="px-4 py-4 font-semibold text-slate-900">{vehicle.make}</td>
                        <td className="px-4 py-4">{vehicle.model}</td>
                        <td className="px-4 py-4">{vehicle.category}</td>
                        <td className="px-4 py-4">
                          {Number(vehicle.price).toLocaleString('en-IN', {
                            style: 'currency',
                            currency: 'INR',
                            maximumFractionDigits: 0,
                          })}
                        </td>

                        <td className="px-4 py-4">{vehicle.quantity}</td>

                        <td className="px-4 py-4">
                          <div className="flex flex-wrap gap-2">
                            {userRole === 'user' && (
                            <button
                              onClick={() => handlePurchase(vehicle.id)}
                              disabled={vehicle.quantity <= 0}
                              className="rounded-lg bg-emerald-700 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-800 disabled:opacity-50"
                            >
                              Purchase
                            </button>
                            )}

                            {userRole === 'admin' && (
                            <button
                              onClick={() => handleEditVehicle(vehicle)}
                              className="rounded-lg bg-amber-600 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-700"
                            >
                              Edit
                            </button>
                            )}

                            {userRole === 'admin' && (
                            <button
                              onClick={() => handleDeleteVehicle(vehicle)}
                              className="rounded-lg bg-red-700 px-3 py-2 text-sm font-semibold text-white hover:bg-red-800"
                            >
                              Delete
                            </button>
                            )}

                            {userRole === 'admin' && (
                            <button
                              onClick={() => handleRestock(vehicle.id)}
                              className="rounded-lg bg-blue-700 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-800"
                            >
                              Restock
                            </button>
                            )}
                          </div>
                        </td>


                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
      <div className="grid w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-xl md:grid-cols-2">
        <section className="flex flex-col justify-center bg-slate-900 p-8 text-white md:p-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-300">
            Dealership Management
          </p>
          <h1 className="mt-5 text-3xl font-bold leading-tight md:text-4xl">
            Car Dealership Inventory System
          </h1>
          <p className="mt-4 leading-7 text-slate-300">
            Manage vehicles, track stock, search inventory, and handle
            purchases in one place.
          </p>
        </section>

        <section className="p-8 md:p-10">
          {!isRegister && (
            <div className="mb-5 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => {
                  setLoginType('admin')
                  setMessage('')
                }}
                className={`rounded-lg px-3 py-2 font-semibold ${loginType === 'admin'
                    ? 'bg-blue-700 text-white'
                    : 'border border-slate-300 text-slate-700'
                  }`}
              >
                Admin Login
              </button>

              <button
                type="button"
                onClick={() => {
                  setLoginType('user')
                  setMessage('')
                }}
                className={`rounded-lg px-3 py-2 font-semibold ${loginType === 'user'
                    ? 'bg-blue-700 text-white'
                    : 'border border-slate-300 text-slate-700'
                  }`}
              >
                User Login
              </button>
            </div>
          )}
          <h2 className="text-2xl font-bold text-slate-900">
            {isRegister ? 'Create your account' : 'Welcome back'}
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            {isRegister
              ? 'Register to access the dealership system.'
              : 'Sign in to view the vehicle inventory.'}
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="username" className="mb-2 block text-sm font-medium text-slate-700">
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                required
                minLength={3}
                maxLength={50}
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                placeholder="Enter your username"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-2 block text-sm font-medium text-slate-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                required
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-700 px-4 py-3 font-semibold text-white hover:bg-blue-800 disabled:opacity-60"
            >
              {loading ? 'Please wait...' : isRegister ? 'Create account' : 'Sign in'}
            </button>
          </form>

          {message && (
            <p role="status" className="mt-5 rounded-lg bg-slate-100 p-3 text-sm text-slate-700">
              {message}
            </p>
          )}

          <p className="mt-6 text-center text-sm text-slate-600">
            {isRegister ? 'Already registered?' : "Don't have an account?"}{' '}
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister)
                setMessage('')
              }}
              className="font-semibold text-blue-700 hover:underline"
            >
              {isRegister ? 'Sign in' : 'Register'}
            </button>
          </p>
        </section>
      </div>
    </div>
  )
}

export default App
