import socket
import threading
import pickle

# Constantes do jogo
BOARD_SIZE = 8
CELL_SIZE = 60
EMPTY, BLACK, WHITE = 0, 1, 2

class OthelloServer:
    
    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.board[3][3], self.board[4][4] = WHITE, WHITE
        self.board[3][4], self.board[4][3] = BLACK, BLACK
        self.current_player = BLACK
        self.game_over = False
        self.clients = []
        self.lock = threading.Lock()

    def handle_surrender(self, surrendering_player):
        with self.lock:
            self.game_over = True
            winner = "Jogador 2" if surrendering_player == BLACK else "Jogador 1"
            player_name = "Jogador 1" if surrendering_player == BLACK else "Jogador 2"
            message = f"Fim de jogo! {player_name} desistiu.\nVencedor: {winner}"
            self.broadcast_message(("GAME_OVER", message))
        
    def start_server(self, host='localhost', port=12345):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(2)
        print("Servidor iniciado. Aguardando conexões...")

        while len(self.clients) < 2:
            client_socket, address = server_socket.accept()
            print(f"Conexão estabelecida com {address}")
            self.clients.append(client_socket)
            client_id = BLACK if len(self.clients) == 1 else WHITE
            
            welcome_msg = pickle.dumps(("WELCOME", "Você jogará com as peças PRETAS" if client_id == BLACK else "Você jogará com as peças BRANCAS"))
            client_socket.sendall(welcome_msg)
            
            threading.Thread(target=self.handle_client, args=(client_socket, client_id)).start()
        
        self.broadcast_game_state()

    def handle_client(self, client_socket, client_id):
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                message = pickle.loads(data)
                if isinstance(message, tuple):
                    message_type, content = message
                    if message_type == "CHAT":
                        player_name = "Jogador 1" if client_id == BLACK else "Jogador 2"
                        self.broadcast_message(("CHAT", f"{player_name}: {content}"))
                    elif message_type == "MOVE":
                        self.handle_move(content)
                    elif message_type == "SURRENDER":
                        self.handle_surrender(client_id)
                else:
                    self.handle_move(message)
                    
            except Exception as e:
                print(f"Erro ao lidar com cliente: {e}")
                break
        
        print(f"Cliente {client_id} desconectado")
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()

    def count_pieces(self):
        black_count = sum(row.count(BLACK) for row in self.board)
        white_count = sum(row.count(WHITE) for row in self.board)
        empty_count = sum(row.count(EMPTY) for row in self.board)
        return black_count, white_count, empty_count

    def check_game_over(self):
        black_count, white_count, empty_count = self.count_pieces()
        board_full = empty_count == 0
        all_same_color = black_count == 0 or white_count == 0

        # Verifica movimentos válidos para ambos os jogadores
        def has_valid_moves(player):
            return any(
                self.is_valid_move(row, col, player)
                for row in range(BOARD_SIZE)
                for col in range(BOARD_SIZE)
            )

        has_valid_moves_black = has_valid_moves(BLACK)
        has_valid_moves_white = has_valid_moves(WHITE)

        # Condições de fim de jogo
        if board_full or all_same_color or (not has_valid_moves_black and not has_valid_moves_white):
            winner = "Jogador 1" if black_count > white_count else "Jogador 2" if white_count > black_count else "EMPATE"
            reason = "Tabuleiro completamente preenchido!" if board_full else \
                    "Todas as peças são da mesma cor!" if all_same_color else \
                    "Não há mais movimentos possíveis!"
            message = f"Fim de jogo! {reason}\nVencedor: {winner}\nPeças pretas: {black_count}\nPeças brancas: {white_count}"
            self.game_over = True
            self.broadcast_message(("GAME_OVER", message))
            return True

        # Verifica se o jogador atual tem movimentos válidos
        current_has_valid_moves = has_valid_moves(self.current_player)

        # Se o jogador atual não tem movimentos, troca o turno
        if not current_has_valid_moves:
            old_player = self.current_player
            self.current_player = WHITE if self.current_player == BLACK else BLACK
            
            # Verifica se o novo jogador tem movimentos válidos
            new_player_has_valid_moves = has_valid_moves(self.current_player)
            
            # Mensagem indicando quem não tem movimentos válidos
            skip_message = (
                "Jogador 2 não tem movimentos válidos. Vez do Jogador 1."
                if old_player == WHITE
                else "Jogador 1 não tem movimentos válidos. Vez do Jogador 2."
            )
            self.broadcast_message(("INFO", skip_message))

            # Se o novo jogador também não tiver movimentos, termina o jogo
            if not new_player_has_valid_moves:
                winner = "Jogador 1" if black_count > white_count else "Jogador 2" if white_count > black_count else "EMPATE"
                message = f"Fim de jogo! Não há mais movimentos possíveis!\nVencedor: {winner}\nPeças pretas: {black_count}\nPeças brancas: {white_count}"
                self.game_over = True
                self.broadcast_message(("GAME_OVER", message))
                return True

            # Atualiza o estado do jogo para refletir a troca de turno
            self.broadcast_game_state()
            return False

        # Continua o jogo normalmente
        return False



    def broadcast_message(self, message):
        msg_data = pickle.dumps(message)
        for client in self.clients:  
            try:
                client.sendall(msg_data)
                print(f"Message sent to client: {client}")
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

    def handle_move(self, move):
        with self.lock:
            row, col, player = move
            
            # Verifica se o jogo já terminou
            if self.game_over:
                return

            # Verifica se é o turno correto do jogador
            if player != self.current_player:
                return

            # Verifica se o movimento é válido para este jogador
            if not self.is_valid_move(row, col, player):
                return

            # Executa o movimento
            self.place_piece(row, col, player)
            self.flip_discs(row, col, player)

            # Alterna o jogador
            self.current_player = WHITE if self.current_player == BLACK else BLACK

            # Transmite o estado do jogo
            self.broadcast_game_state()

            # Verifica condições de fim de jogo e movimentos válidos
            self.check_game_over()

    def broadcast_game_state(self):
        game_state = pickle.dumps(("STATE", (self.board, self.current_player)))
        for client in self.clients:
            client.sendall(game_state)

    def is_valid_move(self, row, col, player):
        if self.board[row][col] != EMPTY:
            return False
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            if self.can_flip(row, col, dr, dc, player):
                return True
        return False

    def can_flip(self, row, col, dr, dc, player):
        r, c = row + dr, col + dc
        opponent = WHITE if player == BLACK else BLACK
        has_opponent_between = False
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            if self.board[r][c] == opponent:
                has_opponent_between = True
            elif self.board[r][c] == player:
                return has_opponent_between
            else:
                break
            r += dr
            c += dc
        return False

    def flip_discs(self, row, col, player):
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            if self.can_flip(row, col, dr, dc, player):
                self.flip_line(row, col, dr, dc, player)

    def flip_line(self, row, col, dr, dc, player):
        r, c = row + dr, col + dc
        opponent = WHITE if player == BLACK else BLACK
        while self.board[r][c] == opponent:
            self.board[r][c] = player
            r += dr
            c += dc

    def place_piece(self, row, col, player):
        self.board[row][col] = player

if __name__ == "__main__":
    server = OthelloServer()
    server.start_server()