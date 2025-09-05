// Express server
const express = require('express');
const app = express();
const cors = require('cors');
const bodyParser = require('body-parser');

app.use(cors());
app.use(bodyParser.json());

app.get('/', (req,res)=>res.send('API Running'));

app.listen(5000, ()=>console.log('Server running on port 5000'));