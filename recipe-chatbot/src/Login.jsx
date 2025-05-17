// template from mdbootstrap

import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  MDBBtn,
  MDBContainer,
  MDBRow,
  MDBCol,
  MDBCard,
  MDBCardBody,
  MDBInput,
  MDBIcon
} from 'mdb-react-ui-kit'
import './Login.css'

export default function Login() {
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]     = useState('')
  const navigate               = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'Login failed')
        return
      }
      localStorage.setItem('access_token', data.access_token)
      console.log('Login success, navigating to home...')
      navigate('/', { replace: true })
    } catch (err) {
      console.error(err)
      setError('Server error')
    }
  }

  return (
    <div className="login-wrapper">
      <MDBContainer>
        <MDBRow className="justify-content-center">
          <MDBCol col="12">
            <MDBCard className="login-card mx-auto my-5">
              <MDBCardBody className="p-5 d-flex flex-column align-items-center w-100 h-100">
                <h2 className="fw-bold mb-2 text-uppercase text-white">Login</h2>
                <p className="text-white-50 mb-5">
                  Please enter your login and password!
                </p>
                <form onSubmit={handleSubmit} style={{ width: '100%' }}>
                  <MDBInput
                    wrapperClass="mb-4 w-100"
                    labelClass="text-white"
                    label="Email address"
                    type="email"
                    size="lg"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                  />
                  <MDBInput
                    wrapperClass="mb-4 w-100"
                    labelClass="text-white"
                    label="Password"
                    type="password"
                    size="lg"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                  />

                  {error && (
                    <p className="text-danger mx-5">{error}</p>
                  )}

                  <div className="d-flex justify-content-center mx-5 mb-4">
                    <MDBBtn outline color="white" size="lg" type="submit" className="login-btn">
                      Login
                    </MDBBtn>
                  </div>
                </form>

                <p className="small mb-0">
                    Don't have an account?{' '}
                    <Link to="/register" className="fw-bold">
                        Sign Up
                    </Link>
                </p>
              </MDBCardBody>
            </MDBCard>
          </MDBCol>
        </MDBRow>
      </MDBContainer>
    </div>
  )
}
