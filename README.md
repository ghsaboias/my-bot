# Monitor de Preço Spot BTCUSDT da Binance
Acompanhe movimentos do preço do Bitcoin na Binance em tempo real.

## Função
Monitora o preço Bitcoin (BTC) para USDT na Binance e alerta sobre mudanças significativas.

## Recursos
- Monitoramento em tempo real via websocket da Binance
- Alertas de variação de preço em 1 segundo, 1 minuto e 5 minutos
- Limiares de variação de preço personalizáveis
- Notificações via Pushover
- Limite na frequência de notificações

## Uso
1. **Configuração do Ambiente**:
   - Certifique-se de ter Python 3.7+ instalado em seu sistema.
   - Clone este repositório para sua máquina local.
   - Instale as dependências necessárias executando `pip install -r requirements.txt` no diretório do projeto.

2. **Configuração do Pushover**:
   - Crie uma conta em [Pushover](https://pushover.net/) se ainda não tiver uma.
   - Após o login, copie sua User Key da página principal.
   - [Crie um novo aplicativo](https://pushover.net/apps/build) no Pushover para obter um API Token.

3. **Configuração do arquivo .env**:
   - Crie um arquivo chamado `.env` no diretório raiz do projeto.
   - Adicione as seguintes linhas ao arquivo, substituindo com suas chaves do Pushover:
     ```
     PUSHOVER_USER_KEY=sua_user_key_aqui
     PUSHOVER_API_TOKEN=seu_api_token_aqui
     ```

4. **Personalização (opcional)**:
   - Abra o arquivo `script.py` em um editor de texto.
   - Modifique os valores de `one_second_threshold`, `one_min_threshold`, e `five_min_threshold` conforme desejado para ajustar os limiares de alerta.
   - Se quiser monitorar outras moedas além do BTC, adicione-as à lista `coins_to_monitor`.

5. **Execução do Script**:
   - Abra um terminal ou prompt de comando.
   - Navegue até o diretório do projeto.
   - Execute o script com o comando `python script.py`.

6. **Monitoramento**:
   - O script começará a monitorar o preço do Bitcoin e enviará notificações via Pushover quando as variações de preço excederem os limiares definidos.
   - Mantenha o script em execução para continuar recebendo atualizações.

## Contribua
Reporte bugs ou sugira melhorias via issues ou pull requests.

## Contato
Para atualizações, dúvidas ou suporte, entre em contato via WhatsApp: +55 11 992745950
