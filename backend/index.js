import express from 'express'
import cors from 'cors'
import driver from './neo4j.js'
import dotenv from 'dotenv'

dotenv.config()
const app = express()
app.use(cors())
app.use(express.json())

const port = process.env.PORT || 4000

app.get('/api/nodes', async (req, res) => {
  const session = driver.session()
  try {
    const result = await session.run('MATCH (n) RETURN n LIMIT 30')
    const nodes = result.records.map(record => record.get('n').properties)
    res.json(nodes)
  } catch (error) {
    console.error(error)
    res.status(500).send('Error querying Neo4j')
  } finally {
    await session.close()
  }
})

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`)
})
