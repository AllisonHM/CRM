# 🎨 Paleta de Cores do CRM - Vendas

## Cores Principais

### Roxo Escuro (Primary)
- **#4a235a** - Roxo Escuro Principal (fundo de headers, botões)
- **#6b3fa0** - Roxo Médio (gradientes)
- **#8b5fbf** - Roxo Claro (hover states)
- **#3a1a4a** - Roxo Mais Escuro (hover escuro)

### Amarelo (Accent)
- **#ffc107** - Amarelo Vibrante (botões secundários, destaque)
- **#ffb300** - Ouro (hover do amarelo)
- **#ffe082** - Amarelo Claro (backgrounds leves)

## Cores Neutras

- **#2c3e50** - Cinza Escuro (texto principal)
- **#ecf0f1** - Cinza Claro (backgrounds)
- **#ffffff** - Branco (cards, inputs)
- **#7f8c8d** - Cinza Médio (texto secundário)

## Cores de Status

- **#27ae60** - Verde Sucesso (alerts, badges)
- **#f39c12** - Laranja Aviso (avisos, atenção)
- **#e74c3c** - Vermelho Perigo (erros, deletar)
- **#3498db** - Azul Informação (informações, dicas)

## Gradientes

```css
/* Primary Gradient */
linear-gradient(135deg, #4a235a 0%, #6b3fa0 100%)

/* Accent Gradient */
linear-gradient(135deg, #ffc107 0%, #ffb300 100%)
```

## Sombras

- **Shadow SM**: 0 2px 4px rgba(74, 35, 90, 0.1)
- **Shadow MD**: 0 4px 12px rgba(74, 35, 90, 0.15)
- **Shadow LG**: 0 8px 24px rgba(74, 35, 90, 0.2)

## Uso das Cores

### Componentes

| Componente | Cor |
|-----------|-----|
| Navbar | Roxo Escuro + Gradiente |
| Headers de Cards | Roxo Escuro + Gradiente |
| Botões Primários | Roxo Escuro |
| Botões Secundários | Amarelo |
| Links | Roxo Escuro (hover: Amarelo) |
| Tabelas (cabeçalho) | Roxo Escuro + Gradiente |
| Badges (sucesso) | Verde |
| Badges (perigo) | Vermelho |
| Backgrounds | Cinza Claro |

## Variáveis CSS Disponíveis

Todas as cores estão disponíveis como variáveis CSS:

```css
--primary-dark: #4a235a;
--primary-medium: #6b3fa0;
--primary-light: #8b5fbf;
--accent-yellow: #ffc107;
--accent-gold: #ffb300;
--accent-light-yellow: #ffe082;
--dark-gray: #2c3e50;
--light-gray: #ecf0f1;
--white: #ffffff;
--text-dark: #2c3e50;
--text-light: #7f8c8d;
--success-green: #27ae60;
--warning-orange: #f39c12;
--danger-red: #e74c3c;
--info-blue: #3498db;
--hover-dark: #3a1a4a;
--hover-yellow: #ffb300;
--shadow-sm: 0 2px 4px rgba(74, 35, 90, 0.1);
--shadow-md: 0 4px 12px rgba(74, 35, 90, 0.15);
--shadow-lg: 0 8px 24px rgba(74, 35, 90, 0.2);
--gradient-primary: linear-gradient(135deg, #4a235a 0%, #6b3fa0 100%);
--gradient-accent: linear-gradient(135deg, #ffc107 0%, #ffb300 100%);
```

## Exemplos de Uso

```html
<!-- Botão Roxo -->
<button class="btn btn-primary">Ação Principal</button>

<!-- Botão Amarelo -->
<button class="btn btn-warning">Ação Secundária</button>

<!-- Card com Header Roxo -->
<div class="card">
  <div class="card-header">Título do Card</div>
  <div class="card-body">Conteúdo</div>
</div>

<!-- Badge de Sucesso -->
<span class="badge badge-success">Sucesso</span>

<!-- Alert -->
<div class="alert alert-success">Mensagem de sucesso</div>
```

## Notas

- A paleta foi escolhida para representar profissionalismo e energia de vendas
- Roxo escuro transmite confiança e sofisticação
- Amarelo vibrante chama atenção para CTAs (Call to Action)
- As cores foram testadas para acessibilidade
- Todos os gradientes usam ângulo de 135deg para visual consistente
