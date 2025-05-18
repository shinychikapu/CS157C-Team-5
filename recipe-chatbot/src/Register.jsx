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
  MDBCheckbox
} from 'mdb-react-ui-kit'
import './Register.css'

export default function Register() {
  const [email, setEmail]   = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]   = useState('')
  const [msg, setMsg]       = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({email, password})
      })
      const data = await res.json()
      if (res.status === 201) {
        setMsg('Registration successful! Redirecting…')
        setTimeout(() => navigate('/', { replace: true }), 1500)
      } else {
        setError(data.detail || 'Registration failed')
      }
    } catch (err) {
      console.error(err)
      setError('Server error')
    }
  }

  return (
    <MDBContainer fluid className="p-4 background-radial-gradient overflow-hidden">
      <MDBRow className="justify-content-center align-items-center vh-100">
        <MDBCol md="6" className="d-flex justify-content-center align-items-center position-relative">
        <h1 className="my-5 display-3 fw-bold ls-tight px-3" style={{ color: 'hsl(218,81%,95%)' }}>
            Register <br />
            <span style={{ color: 'hsl(218,81%,75%)' }}></span>
        </h1>
        <p className="px-3" style={{ color: 'hsl(218,81%,85%)' }}></p>
        </MDBCol>

        <MDBCol md="6" className="d-flex justify-content-center align-items-center vh-100 position-relative">
          <div id="radius-shape-1" className="position-absolute rounded-circle shadow-5-strong"></div>
          <div id="radius-shape-2" className="position-absolute shadow-5-strong"></div>

          <MDBCard className="my-5 bg-glass">
            <MDBCardBody className="p-5">
              <form onSubmit={handleSubmit}>
                <MDBRow>
                </MDBRow>
                <MDBInput
                  wrapperClass="mb-3"
                  label="Email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                />
                <MDBInput
                  wrapperClass="mb-3"
                  label="Password"
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />

                {error && <p className="text-danger my-1">{error}</p>}
                {msg && <p className="text-success my-1">{msg}</p>}

                <MDBBtn className="w-100 mb-4" size="md" type="submit">
                  Sign up
                </MDBBtn>
              </form>

              <p className="text-center">
                Already have an account?{' '}
                <Link to="/login" className="fw-bold">
                  Login
                </Link>
              </p>
            </MDBCardBody>
          </MDBCard>
        </MDBCol>
      </MDBRow>
    </MDBContainer>
  )
}
