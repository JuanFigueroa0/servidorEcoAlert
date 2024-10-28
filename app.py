from flask import Flask, request, jsonify
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os
from flask_cors import CORS

# Cargar variables de entorno desde el archivo .env
#load_dotenv(dotenv_path="/Juan Figueroa/Descargas 2/EcoAlert/ecoalert/lib/bd.env")

# Configurar Flask
app = Flask(__name__)
CORS(app, resources={r"/report": {"origins": "*"}})  # Habilitar CORS para cualquier origen

# Configurar MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['ecoalert']  # Usar la base de datos 'ecoalert'
reports_collection = db['reports']

# Configurar Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Ruta para crear un nuevo reporte
@app.route('/report', methods=['POST'])
def create_report():
    try:
        # Mostrar logs para ver qué se está recibiendo desde el cliente
        print("Datos recibidos:", request.form)
        print("Archivos recibidos:", request.files)

        # Obtener la descripción desde el formulario
        description = request.form.get('description')
        if not description:
            return jsonify({'error': 'La descripción es requerida'}), 400

        # Obtener los datos de la dirección desde el formulario
        address = request.form.get('address')  # Dirección completa enviada por el frontend
        if not address:
            return jsonify({'error': 'La dirección es requerida'}), 400

        # Obtener la localidad, barrio y correo electrónico
        localidad = request.form.get('localidad')  # Nueva línea para obtener la localidad
        barrio = request.form.get('barrio')  # Nueva línea para obtener el barrio
        correo_electronico = request.form.get('correoElectronico')  # Nueva línea para obtener el correo electrónico

        # Validar los nuevos campos
        if not localidad:
            return jsonify({'error': 'La localidad es requerida'}), 400
        if not barrio:
            return jsonify({'error': 'El barrio es requerido'}), 400
        if not correo_electronico:
            return jsonify({'error': 'El correo electrónico es requerido'}), 400

        # Subir la imagen a Cloudinary
        if 'image' not in request.files:
            return jsonify({'error': 'Imagen es requerida'}), 400

        image_file = request.files['image']
        try:
            upload_result = cloudinary.uploader.upload(image_file)
        except Exception as e:
            return jsonify({'error': f'Error al subir la imagen a Cloudinary: {e}'}), 500

        # Guardar los datos en MongoDB
        report = {
            'description': description,
            'full_address': address,  # Guardar la dirección completa
            'localidad': localidad,  # Agregar la localidad
            'barrio': barrio,  # Agregar el barrio
            'correo_electronico': correo_electronico,  # Agregar el correo electrónico
            'image_url': upload_result['secure_url'],
            'created_at': upload_result['created_at']
        }

        result = reports_collection.insert_one(report)
        report['_id'] = str(result.inserted_id)

        return jsonify({'message': 'Reporte creado correctamente', 'report': report}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ruta para obtener todos los reportes
@app.route('/reports', methods=['GET'])
def get_reports():
    try:
        reports = list(reports_collection.find({}, {'_id': 1, 'description': 1,'full_address': 1, 'localidad': 1, 'barrio': 1, 'correo_electronico': 1, 'image_url': 1, 'created_at': 1}))
        for report in reports:
            report['_id'] = str(report['_id'])  # Convertir ObjectId a string para evitar problemas en el frontend
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
