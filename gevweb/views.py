import subprocess, os, mimetypes
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from wsgiref.util import FileWrapper
from django.utils.encoding import smart_str
from sklearn.cluster import AgglomerativeClustering
import pandas as pd
import numpy as np


from gevweb.forms import DocumentForm
from gevweb.models import Document

def index(request):
	if request.method == 'POST':
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			documents = list(Document.objects.all().values_list('document',flat=True))
			f_names=[]
			if documents!=[]:
				for i in documents:
					i=i.split('/')[1]
					f_names.append(i)
			gef_name=f_names[0]
			request.session['gef_name']=gef_name
			if len(f_names)==1:
				ff_name=None
			else:
				ff_name=f_names[1]
				request.session['ff_name']=ff_name
			return render(request, 'gevweb/index.html', {'form': form, 'gef_name':gef_name, 'ff_name':ff_name})
	else:
		form = DocumentForm()
		documents = list(Document.objects.all().values_list('document',flat=True))
		if documents!=[]:
			i_clean=Document.objects.all().delete()
			documents=[]
			go_to_data_folder_command='cd '+settings.MEDIA_ROOT+'\\'+'gev_data_to_use'
			clean_previous_data_command=go_to_data_folder_command+' && '+'del * /S /Q'
			clean_previous_data=subprocess.check_output(clean_previous_data_command, shell=True).decode("utf-8").replace('\r\n','')
		return render(request, 'gevweb/index.html', {'form': form, 'documents':documents})
	
def analyze(request):
	if request.method == 'POST':
		'''process data from website'''
		num_of_clusters=request.POST.get('n_clusters')
		if num_of_clusters=='':
			num_of_clusters=10
		else:
			num_of_clusters=int(num_of_clusters)
		linkage=request.POST.get('linkage')
		
		'''get data passed from previous page'''
		gef_name=request.session.get('gef_name')
		ff_name=request.session.get('ff_name')
		data_path=settings.MEDIA_ROOT+'\\'+'gev_data_to_use'
		'''read and pre-process GE data'''
		data = pd.read_csv(data_path+'\\'+gef_name,index_col=0,sep=',')
		data=data.transpose()
		index=list(data.index.values)
		data=data.values
		'''run agglomerative cluster algorithm'''
		clustering = AgglomerativeClustering(linkage=linkage, n_clusters=num_of_clusters)
		clustering.fit(data)
		'''get ids for each cluster'''
		cluster_labels=clustering.labels_
		ids_each_cluster=[]
		for m in range(num_of_clusters):
			c_index=np.where(cluster_labels==m)[0]
			id_list=[index[i] for i in c_index]
			ids_each_cluster.append(id_list)
		'''read and pre-process feature data'''
		feature=pd.read_csv(data_path+'\\'+ff_name,index_col=0,sep=',')
		feature[feature.select_dtypes(['object']).columns] = feature.select_dtypes(['object']).apply(lambda x: x.astype('category'))
		feature_index_list=list(feature)
		'''proces result from clustering, replace numbers with symbol'''
		rows_data=[]
		for attribute in list(feature):
			if str(feature[attribute].dtype)=='category':
				row_data=[]
				for j in ids_each_cluster:
					row_data.append(feature[attribute][j].dropna().cat.codes.mean())
				one_thrid_gap=(max(row_data)-min(row_data))/3
				min_row=min(row_data)
				max_row=max(row_data)
				for k in range(len(row_data)):
					if row_data[k] < min_row+one_thrid_gap:
						row_data[k]='+'
					elif row_data[k] > max_row-one_thrid_gap:
						row_data[k]='+++'
					else:
						row_data[k]='++'    
			else:
				row_data=[]
				for j in ids_each_cluster:
					row_data.append(feature[attribute][j].dropna().mean())
				one_thrid_gap=(max(row_data)-min(row_data))/3
				min_row=min(row_data)
				max_row=max(row_data)
				for k in range(len(row_data)):
					if row_data[k] < min_row+one_thrid_gap:
						row_data[k]='+'
					elif row_data[k] > max_row-one_thrid_gap:
						row_data[k]='+++'
					else:
						row_data[k]='++'    
			rows_data.append(row_data)
		'''get data ready for a table in html'''
		#prepare head
		head=['     ']
		for x in range(num_of_clusters):
			head.append('Cluster '+str(x+1))
		#prepare data in each row
		for y in range(len(rows_data)):
			rows_data[y]=[feature_index_list[y]]+rows_data[y]	
		return render(request, 'gevweb/analyze.html', {'head':head,'rows_data': rows_data, 'num_of_clusters':num_of_clusters, 'linkage':linkage})
	else:
		see=['empty']
		return render(request, 'gevweb/analyze.html', {'see': see})
		
	
def download_sample(request,file_name):
	data_path = settings.MEDIA_ROOT
	file_path = data_path+'\\'+file_name
	file_wrapper = FileWrapper(open(file_path))
	file_mimetype = mimetypes.guess_type(file_path)
	response = HttpResponse(file_wrapper, content_type=file_mimetype )
	response['X-Sendfile'] = file_path
	response['Content-Length'] = os.stat(file_path).st_size
	response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name) 
	return response