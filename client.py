# Cliente (OthelloGameClient.py)
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import socket
import threading
import pickle
import sys

# Constantes do jogo
BOARD_SIZE = 8
CELL_SIZE = 60
EMPTY, BLACK, WHITE = 0, 1, 2
BOARD_COLOR = "#007f21"
PIECE_COLORS = {BLACK: "black", WHITE: "white"}
WOOD_COLOR = "#8B4513"
HIGHLIGHT_COLOR = "#005416"
TRANSPARENT_COLOR = "#ffffff80"
BORDER_COLOR = "#333333"


class OthelloGameClient:
    def __init__(self, root, player, player_name, host='localhost', port=12345):
        self.root = root
        self.root.title(player_name)
        self.player = player
        self.current_player = BLACK
        
        # Criar frame principal
        main_frame = ttk.Frame(root)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Frame esquerdo para o tabuleiro
        board_frame = ttk.Frame(main_frame)
        board_frame.pack(side='left', padx=5)
        
        # Frame direito para o chat
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        # Área de chat
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=40, height=20)
        self.chat_display.pack(fill='both', expand=True, pady=5)
        
        # Frame para entrada de mensagem
        message_frame = ttk.Frame(chat_frame)
        message_frame.pack(fill='x', pady=5)
        
        self.message_entry = ttk.Entry(message_frame)
        self.message_entry.pack(side='left', fill='x', expand=True)
        
        send_button = ttk.Button(message_frame, text="Enviar", command=self.send_message)
        send_button.pack(side='right', padx=5)
        
        # Botão de desistência
        surrender_button = ttk.Button(message_frame, text="Desistir", 
                                      command=self.surrender, 
                                      style='Danger.TButton')
        surrender_button.pack(side='right', padx=5)
        
        # Configurar estilo do botão de desistência
        style = ttk.Style()
        style.configure('Danger.TButton', foreground='red')
        
        # Bind Enter key to send message
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        # Canvas para o tabuleiro (restante do código igual)
        canvas_width = (BOARD_SIZE + 2) * CELL_SIZE
        canvas_height = (BOARD_SIZE + 2) * CELL_SIZE
        self.canvas = tk.Canvas(board_frame, width=canvas_width, height=canvas_height)
        self.canvas.pack()

        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.draw_board()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        threading.Thread(target=self.receive_data).start()
        self.canvas.bind("<Button-1>", self.handle_click)

    def surrender(self):
        # Confirmar desistência
        if self.player != self.current_player:
            messagebox.showwarning("Aviso", "Não é sua vez de jogar.")
            return
        
        resposta = messagebox.askyesno("Confirmação", 
                                       "Tem certeza que deseja desistir?")
        if resposta:
            self.socket.sendall(pickle.dumps(("SURRENDER", None)))
            messagebox.showinfo("Desistência", "Você desistiu do jogo.")

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            self.socket.sendall(pickle.dumps(("CHAT", message)))
            self.message_entry.delete(0, tk.END)

    def handle_click(self, event):
        
        print(f"Player={self.player}, CurrentPlayer={self.current_player}")
        # Verifica se o jogo terminou
        if hasattr(self, 'game_over') and self.game_over:
            messagebox.showwarning("Aviso", "O jogo já terminou.")
            return

        # Verifica se é a vez do jogador
        if self.player != self.current_player:
            messagebox.showwarning("Aviso", "Não é sua vez de jogar.")
            return

        # Calcula a posição do clique no tabuleiro
        col = (event.x // CELL_SIZE) - 1
        row = (event.y // CELL_SIZE) - 1

        # Verifica se o clique está dentro do tabuleiro
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            # Verifica se o movimento é válido antes de enviar
            if self.is_valid_move(row, col, self.player):
                move_data = (row, col, self.player)
                self.socket.sendall(pickle.dumps(("MOVE", move_data)))
            else:
                messagebox.showwarning("Aviso", "Movimento inválido.")

    def receive_data(self):
        while True:
            try:
                data = self.socket.recv(4096)
                message_type, content = pickle.loads(data)
                print(f"Received message: {message_type}, {content}")
                
                if message_type == "WELCOME":
                    messagebox.showinfo("Bem-vindo", content)
                elif message_type == "GAME_OVER":
                    self.game_over = True
                    messagebox.showinfo("Fim de Jogo", content)
                    self.socket.close() 
                    self.root.destroy() 
                elif message_type == "INFO":
                    # Extrair informação de quem não tem movimentos
                    if "não tem movimentos válidos" in content:
                        # Extrair o próximo jogador da mensagem
                        next_player = BLACK if "Vez do Jogador 1" in content else WHITE
                        self.current_player = next_player
                        print(f"INFO: Atualizando current_player para {next_player}")
                        self.draw_pieces()
                        self.highlight_valid_moves()
                    messagebox.showinfo("Aviso", content)
                elif message_type == "CHAT":
                    self.chat_display.insert(tk.END, content + '\n')
                    self.chat_display.see(tk.END)
                elif message_type == "STATE":
                    print(f"Received STATE: Current Player {content[1]}")
                    self.board, server_current_player = content
                    
                    # Verificar e atualizar o jogador atual
                    if server_current_player != self.current_player:
                        print(f"Mudando jogador de {self.current_player} para {server_current_player}")
                        self.current_player = server_current_player
                    
                    self.draw_pieces()
                    self.highlight_valid_moves()
            except Exception as e:
                print(f"Erro ao receber dados: {e}")
                break
                
    def draw_board(self):
        self.canvas.create_rectangle(
            CELL_SIZE * 0.5, CELL_SIZE * 0.5, (BOARD_SIZE + 1.5) * CELL_SIZE, (BOARD_SIZE + 1.5) * CELL_SIZE,
            fill=WOOD_COLOR, outline=WOOD_COLOR
        )
        self.canvas.create_rectangle(
            CELL_SIZE, CELL_SIZE, (BOARD_SIZE + 1) * CELL_SIZE, (BOARD_SIZE + 1) * CELL_SIZE,
            fill=BOARD_COLOR, outline=""
        )
        for col in range(BOARD_SIZE):
            x = (col + 1) * CELL_SIZE + CELL_SIZE // 2
            self.canvas.create_text(x, CELL_SIZE * 0.75, text=chr(65 + col), font=("Arial", 12, "bold"), fill="white")
        for row in range(BOARD_SIZE):
            y = (row + 1) * CELL_SIZE + CELL_SIZE // 2
            self.canvas.create_text(CELL_SIZE * 0.75, y, text=str(row + 1), font=("Arial", 12, "bold"), fill="white")
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1, y1 = (col + 1) * CELL_SIZE, (row + 1) * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")

    def draw_pieces(self):
        self.canvas.delete("piece")
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] != EMPTY:
                    self.draw_piece(row, col, self.board[row][col])
    
    def draw_piece(self, row, col, piece_color):
        x1 = (col + 1) * CELL_SIZE + 5
        y1 = (row + 1) * CELL_SIZE + 5
        x2 = x1 + CELL_SIZE - 10
        y2 = y1 + CELL_SIZE - 10
        self.canvas.create_oval(x1, y1, x2, y2, fill=PIECE_COLORS[piece_color], outline=PIECE_COLORS[piece_color], tags="piece")

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

    def highlight_valid_moves(self):
        self.canvas.delete("highlight")
        if self.player == self.current_player:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.is_valid_move(row, col, self.current_player):
                        x1 = (col + 1) * CELL_SIZE + 5
                        y1 = (row + 1) * CELL_SIZE + 5
                        x2 = x1 + CELL_SIZE - 10
                        y2 = y1 + CELL_SIZE - 10
                        self.canvas.create_oval(x1, y1, x2, y2, fill=HIGHLIGHT_COLOR, outline="", tags="highlight")

def main():
    root = tk.Tk()
    player_arg = sys.argv[1] if len(sys.argv) > 1 else "2"
    player = BLACK if player_arg == "1" else WHITE
    player_name = "JOGADOR 1" if player_arg == "1" else "JOGADOR 2"
    game = OthelloGameClient(root, player, player_name)
    root.mainloop()

if __name__ == "__main__":
    main()