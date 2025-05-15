const express = require('express');
const passport = require('passport');
const GithubStrategy = require('passport-github2').Strategy;
const session = require('express-session');
require('dotenv').config();

const app = express();

// Configuração da sessão
app.use(session({ secret: 'segredo', resave: false, saveUninitialized: false }));

// Inicialização do Passport
app.use(passport.initialize());
app.use(passport.session());

// Serialização
passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

// Estratégia do GitHub
passport.use(new GithubStrategy({
    clientID: "Ov23ct3aHuEs4IxDYQmv",
    clientSecret: "58f97dea08f18e68d01bb29b5b6b87f7d2cc57b2",
    callbackURL: "http://localhost:3000/auth/github/callback"
  },
  function(accessToken, refreshToken, profile, done) {
    return done(null, profile);
  }
));

// Rotas
app.get('/', (req, res) => {
  if (req.isAuthenticated()) {
    res.send(`<h1>Olá, ${req.user.displayName || req.user.username}!</h1>`);
  } else {
    res.send('<a href="/auth/github">Login com GitHub</a>');
  }
});

app.get('/auth/github', passport.authenticate('github', { scope: ['user:email'] }));

app.get('/auth/github/callback', 
  passport.authenticate('github', { failureRedirect: '/' }),
  (req, res) => res.redirect('/')
);

// Logout
app.get('/logout', (req, res) => {
  req.logout(() => res.redirect('/'));
});

app.listen(3000, () => console.log('App rodando em http://localhost:3000'));
