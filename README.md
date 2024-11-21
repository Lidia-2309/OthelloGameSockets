# Othello (Reversi) com Sockets - Jogo Multijogador

Este é um projeto de implementação do jogo Othello (Reversi) utilizando sockets para permitir que dois jogadores joguem de forma remota. O servidor gerencia a lógica do jogo e a comunicação entre os jogadores, enquanto o cliente é responsável pela interface gráfica e pela interação com o jogador.

## Como Executar

Para rodar o jogo, siga os seguintes passos:

### 1. Executar o Servidor
Primeiro, inicie o servidor, que ficará aguardando as conexões dos jogadores.

```bash
python server.py
```

### 2. Executar os Clientes
Em seguida, execute o cliente para os dois jogadores, onde cada um deve especificar seu número de jogador (1 ou 2).

```bash
python client.py 1
python client.py 2
```

O jogador 1 receberá as peças pretas, e o jogador 2 receberá as peças brancas.

## Principais Funções

### Server

- **`start_server()`**: Inicializa o servidor, aguarda a conexão de dois clientes e inicia o jogo.
- **`handle_client()`**: Lida com a comunicação de cada cliente, processando suas jogadas e mensagens de chat.
- **`handle_move()`**: Processa uma jogada de um jogador, verificando se ela é válida e atualizando o estado do tabuleiro.
- **`broadcast_message()`**: Envia uma mensagem para todos os clientes conectados.
- **`check_game_over()`**: Verifica se o jogo terminou, seja por vitória, empate ou falta de movimentos válidos.
- **`handle_surrender()`**: Processa a desistência de um jogador, finalizando o jogo e declarando o vencedor.
- **`broadcast_game_state()`**: Envia o estado atual do jogo (tabuleiro e turno) para todos os clientes.

### Client

- **`OthelloGameClient`**: Classe principal que define a interface gráfica do jogo utilizando `tkinter`. Ela lida com a exibição do tabuleiro, o chat e a interação com o servidor.
- **`update_board()`**: Atualiza a exibição do tabuleiro na interface gráfica, refletindo o estado atual do jogo.
- **`handle_click()`**: Gerencia o clique do jogador no tabuleiro, enviando a jogada para o servidor caso o movimento seja válido. Além disso, destaca a célula selecionada para o movimento.
- **`receive_data()`**: Adiciona o processamento de mensagens recebidas do servidor, atualizando o estado do jogo e da interface conforme o tipo de mensagem. Lida com mensagens de boas-vindas, término de jogo, informações do jogo, mensagens de chat e o estado atual do tabuleiro e jogadores.
- **`send_move()`**: Envia uma jogada do jogador para o servidor.
- **`send_chat_message()`**: Envia uma mensagem de chat para o servidor.
- **`receive_message()`**: Recebe mensagens do servidor e as exibe no chat ou atualiza o estado do jogo.
- **`show_message()`**: Exibe uma janela de mensagem para alertar o jogador sobre o estado do jogo (como vitória ou fim de jogo).

## Sobre o Jogo

### Objetivo

O objetivo do jogo é ter mais peças da sua cor no tabuleiro ao final da partida. O jogo é jogado em um tabuleiro 8x8, com peças pretas e brancas. O jogador com as peças pretas começa a partida e pode colocar uma peça em qualquer posição válida. As peças do adversário entre a peça recém-colocada e outra peça do mesmo jogador são viradas.

A partida termina quando nenhum dos jogadores puder fazer movimentos válidos ou quando todas as casas estiverem ocupadas. O vencedor é o jogador com mais peças de sua cor no tabuleiro, ou o jogo termina em empate se houver o mesmo número de peças.

### Regras

1. **Turnos**: O jogo é jogado em turnos alternados entre os jogadores.
2. **Movimentos válidos**: Um movimento é válido se ele virá uma ou mais peças do adversário entre a peça colocada e outra peça do jogador na mesma linha (horizontal, vertical ou diagonal).
3. **Fim de Jogo**: O jogo termina quando nenhum dos jogadores puder fazer movimentos válidos, quando o tabuleiro estiver cheio ou quando todas as peças forem da mesma cor.

### Funcionalidades Básicas

- Controle de turno (quem inicia a partida).
- Movimentação de peças no tabuleiro.
- Desistência de um jogador, resultando no fim do jogo.
- Chat para comunicação entre os jogadores durante a partida.
- Detecção de vencedor (baseado no número de peças de cada jogador).
