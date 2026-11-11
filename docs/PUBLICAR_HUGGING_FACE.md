# Publicar a demo no Hugging Face Spaces

A demo fica online e com link para colocar no currículo. O plano gratuito basta.

1. Crie uma conta em [huggingface.co](https://huggingface.co/join).
2. Clique em **New Space** e preencha:
   - **Space name:** `airflow-log-assistant`
   - **SDK:** Gradio
   - **Hardware:** CPU basic (gratuito)
   - **Visibility:** Public
3. Na página do Space, abra **Files** e envie estes itens do repositório:
   `app.py`, `requirements.txt`, a pasta `assistant/` e a pasta `data/`.
4. Edite o `README.md` do Space e mantenha o bloco de configuração no topo, por exemplo:

   ```yaml
   ---
   title: Airflow Log Assistant
   emoji: 🛠️
   colorFrom: blue
   colorTo: green
   sdk: gradio
   app_file: app.py
   pinned: false
   ---
   ```

5. Opcional, para usar a LLM: em **Settings > Variables and secrets**, clique em **New secret**, use o nome `GEMINI_API_KEY` e cole sua chave. Use secret, nunca variável pública.
6. Espere o build terminar (alguns minutos) e teste os logs de exemplo.
7. Copie o link do Space e coloque no topo do `README.md` do GitHub, no LinkedIn e no currículo.

Se o build falhar, abra a aba **Logs** do Space; o erro costuma ser uma pasta que não foi enviada.
