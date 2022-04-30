#!/usr/bin/python

## IMPORTS
from ftplib import FTP
import subprocess
import os

## COLORS
BOLD_RED    = "\033[1;31m"
BOLD_GREEN  = "\033[1;32m"
BOLD_YELLOW = "\033[1:33m"
BOLD_STYLE  = "\033[1m"
ENDCOLOR    = "\033[0m"

## FUNCTIONS
def HAS_ROOT_PRIV():
	is_root = True
	if os.getuid() != 0:
		is_root = False
	return is_root

def STATUS( status_msg , msg , color):
	return "{}[ {}{} {}{}] -{} {}".format(
		BOLD_STYLE,
		color,
		status_msg,
		ENDCOLOR,
		BOLD_STYLE,
		ENDCOLOR,
		msg)

## MAIN
# CONTANTS
STATUS_CODE = 0
FTP_IP      = "192.168.1.44"
FTP_USUARIO = "luismen"
FTP_CONTRA  = "luismenfana"
FTP_BACKUP_DIR = "apache_copia"
APACHE_ROOT = "/var/www/html/"
#LISTA donde guardo los archivos de APACHE_ROOT
FILES = []

# COMPROBAR SI SE EJECUTA CON SUDO O ROOT
if not HAS_ROOT_PRIV():
	print(STATUS("ERROR", "No root privileges...",BOLD_RED))
	exit(1)

# VER SI APACHE2 ESTA ACTIVO
apache2_active = subprocess.Popen("systemctl is-active apache2".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
apache2_active = apache2_active.stdout.read().strip().decode("utf-8")

if apache2_active == 'inactive':
	print(STATUS("OK", "apache2 is ALREADY STOPPED...", BOLD_GREEN))
else:
	# SI ESTA ACTIVO, LO PARAMOS
	print(STATUS("INFO", "apache2 is running. Stopping it...", BOLD_YELLOW))
	STATUS_CODE = os.system("systemctl stop apache2")
	if STATUS_CODE == 0:
		print(STATUS("OK", "apache2 has been stopped.", BOLD_GREEN))
	else:
		print(STATUS("ERROR", "Errors while stopping apache2",BOLD_RED))
		print(STATUS("ERROR", "Exiting...",BOLD_RED))
		exit(1)

# INICIAR CONEXIÓN FTP
print()
try:
	print(STATUS("OK", "FTP. Attemting to connect to {}".format(FTP_IP),BOLD_GREEN))
	ftp = FTP(FTP_IP)
	print(STATUS("OK", "FTP. Login to {} account...".format(FTP_USUARIO),BOLD_GREEN))
	ftp.login(FTP_USUARIO, FTP_CONTRA)
	# CONEXIÓN FTP ESTABLECIDA CON ÉXITO
	print(STATUS("OK", "FTP. Changing directory to {}...".format(FTP_BACKUP_DIR),BOLD_GREEN))
	ftp.cwd(FTP_BACKUP_DIR)
except:
	print(STATUS("ERROR", "Errors while trying to connect {}".format(FTP_IP),BOLD_RED))
	print(STATUS("ERROR", "Exiting...",BOLD_RED))
	exit(1)

# LISTAR ARCHIVOS DE APACHE_ROOT y METERLO EN la LISTA FILES
print()
print(STATUS("OK", "Listing ALL files in {}".format(APACHE_ROOT),BOLD_GREEN))
files_count = 0
for root,dir,dirfiles in os.walk(APACHE_ROOT):
	for file in dirfiles:
		files_count = files_count + 1
		fullpath_file = os.path.join(root, file)
		print("   "+fullpath_file)
		FILES.append(fullpath_file)
print(STATUS("DONE", "Found {} files in {}".format(files_count,APACHE_ROOT),BOLD_GREEN))

# RECORRER LA LISTA DE ARCHIVOS, CREAR EL DIRECTORIO SI ES PRECISO
#Y ENVIAR EL ARCHIVO
print()
pushed_files_count = 0
for file in FILES:
	basename       = file.replace(APACHE_ROOT, '')
	ftp_files_list = ftp.nlst()
	dir 		   = os.path.dirname(basename)
	# CREAR DIRECTORIO REMOTO
	if dir != '' and dir not in ftp_files_list:
		print(STATUS("INFO","{} directory doesn't exist. Will be created.".format(dir),BOLD_YELLOW))
		try:
			ftp.mkd(dir)
		except:
			print(STATUS("ERROR", "Error while creating {} directory.".format(dir),BOLD_RED))
			print(STATUS("ERROR", "Exiting...",BOLD_RED))
			exit(1)
	#ENVIAR EL ARCHIVO
	try:
		print(STATUS("INFO","Pushing {} to {}...".format(
			file,os.path.join("/",FTP_BACKUP_DIR,basename)
		),BOLD_YELLOW))
		with open(file, 'rb') as text_file:
			ftp.storlines('STOR {}'.format(basename), text_file)
			print(STATUS("OK", "PUSHED {}".format(file),BOLD_GREEN))
			pushed_files_count += 1
	except:
		print(STATUS("ERROR", "Error while pushing {} to {}.".format(
            file,os.path.join("/",FTP_BACKUP_DIR,basename)
        ),BOLD_RED))

# MOSTRAR EL NUMERO DE ARCHIVO QUE SE TENIAN QUE ENVIAR
# Y LOS QUE HAN SIDO ENVIADOS CON EXITO
print()
if pushed_files_count < files_count:
	print(STATUS("INFO","{} out of {} were correctly pushed.".format(pushed_files_count,files_count),BOLD_YELLOW))
else:
	print(STATUS("OK","{} out of {} were correctly pushed.".format(pushed_files_count,files_count),BOLD_GREEN))

# INICIAR APACHE PK ESTAVA STOPPED
print()
print(STATUS("INFO", "Starting apache2...", BOLD_YELLOW))
STATUS_CODE = os.system("systemctl start apache2")
if STATUS_CODE == 0:
    print(STATUS("OK", "apache2 has been started.", BOLD_GREEN))
else:
    print(STATUS("ERROR", "Errors while starting apache2",BOLD_RED))
    print(STATUS("ERROR", "Exiting...",BOLD_RED))
    exit(1)


# CERRAR FTP
ftp.quit()
