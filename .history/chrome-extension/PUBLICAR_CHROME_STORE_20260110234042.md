# Como Publicar no Chrome Web Store

## 📋 Checklist de Preparação

### 1. Conta de Desenvolvedor

- [ ] Acesse: https://chrome.google.com/webstore/devconsole
- [ ] Pague taxa única de **$5 USD**
- [ ] Verifique seu email

### 2. Assets Necessários

#### Ícones (✅ Já criados)

- `icons/icon16.png` - 16x16px
- `icons/icon48.png` - 48x48px
- `icons/icon128.png` - 128x128px

#### Screenshots (📸 Precisa criar)

Tire screenshots da extensão em uso:

- **Tamanho:** 1280x800 ou 640x400 pixels
- **Mínimo:** 1 screenshot
- **Máximo:** 5 screenshots
- **Formato:** PNG ou JPEG

**Dica:** Abra a extensão, faça uma busca, e tire print com:

```bash
# Linux - área selecionada
gnome-screenshot -a -f screenshot1.png

# Ou use Flameshot
flameshot gui
```

#### Imagem Promocional (Opcional mas recomendado)

- **Pequena:** 440x280 pixels
- **Marquee:** 1400x560 pixels

### 3. Criar o ZIP

```bash
cd /mnt/Dados1/APP_Download_Video_Youtube/chrome-extension
zip -r youtube-search-pro.zip manifest.json popup.html popup.js styles.css icons/
```

---

## 🚀 Publicação

### Passo 1: Acessar o Console

1. Vá para https://chrome.google.com/webstore/devconsole
2. Clique em **"Novo item"**

### Passo 2: Upload do ZIP

1. Faça upload do `youtube-search-pro.zip`
2. Aguarde processamento

### Passo 3: Preencher informações

#### Listagem da Loja

- **Idioma:** Português (Brasil)
- **Nome:** YouTube Search Pro
- **Descrição curta:** Busque vídeos do YouTube diretamente do navegador
- **Descrição completa:** (veja abaixo)
- **Categoria:** Produtividade
- **Idioma:** Português

#### Descrição Completa (copie isso):

```
🔍 YouTube Search Pro - Busca Rápida de Vídeos

Pesquise vídeos do YouTube diretamente do seu navegador, sem precisar abrir uma nova aba!

✨ RECURSOS:
• Busca instantânea de vídeos do YouTube
• Thumbnails em alta qualidade
• Informações completas: duração, views, canal, data
• Scroll infinito - carrega mais resultados automaticamente
• Tema escuro moderno
• Lembra sua última busca
• Interface limpa e intuitiva

🚀 COMO USAR:
1. Clique no ícone da extensão
2. Digite sua busca
3. Clique no vídeo para abrir no YouTube

⚡ RÁPIDO E LEVE:
• Não coleta dados pessoais
• Sem anúncios
• Sem rastreamento
• 100% gratuito

Desenvolvido com ❤️ para quem quer praticidade!
```

### Passo 4: Gráficos

- Upload das screenshots
- Upload do ícone 128x128

### Passo 5: Práticas de Privacidade

- **Uso de dados:** Não coleta dados do usuário
- **Veja o arquivo:** privacy-policy.md

### Passo 6: Enviar para Revisão

1. Clique em **"Enviar para revisão"**
2. Aguarde 1-3 dias úteis
3. Você receberá email quando aprovada

---

## ⚠️ Dicas Importantes

1. **Primeira publicação** pode demorar mais (até 1 semana)
2. **Atualizações** são mais rápidas (1-2 dias)
3. **Rejeição comum:** Descrição vaga ou screenshots ruins
4. **Host permissions:** Justifique por que precisa acessar youtube.com

### Justificativa para Permissões (use no formulário):

```
A extensão precisa acessar youtube.com para:
1. Buscar vídeos baseado na pesquisa do usuário
2. Extrair informações públicas dos resultados (título, thumbnail, duração)
3. Não coleta nem armazena dados pessoais do usuário
```

---

## 📞 Suporte

Se a extensão for rejeitada, você receberá um email explicando o motivo.
Motivos comuns:

- Screenshots de baixa qualidade
- Descrição muito curta
- Ícone não segue as diretrizes
- Funcionalidade não clara

Boa sorte! 🎉
