from __future__ import unicode_literals
import xlwt
import json
from .. models import Project, Site
from .. rolemixins import DonorRoleMixin, ProjectRoleMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from onadata.apps.eventlog.models import FieldSightLog, CeleryTaskProgress
from onadata.apps.fieldsight.tasks import importSites
from django.http import HttpResponse
from rest_framework import status


def parse_form_response(main_question, main_answer):

    parsed_question=[]
    parsed_answer=[]
    media_folder =''
    base_url=''

    def append_row( question_name, question_label, question_type, answer_dict):
    
        if question_name in answer_dict:
            if question_type == 'note':
                answer=''
                
            elif question_type == 'photo':
                answer = 'http://'+base_url+'/media/'+ media_folder +'/attachments/'+ answer_dict[question_name]
                
            elif question_type == 'audio' or question_type == 'video':
                answer = 'http://'+base_url+'/media/'+ media_folder +'/attachments/'+ answer_dict[question_name]
                
            else:
                answer=answer_dict[question_name]

        else:
            answer=''
        
        parsed_question.append({'question_name':question_name, 'question_label':question_label})
        parsed_answer.append({question_name:answer})

    def parse_repeat( r_object):
        
        r_question = r_object['name']
        for r_answer in main_answer[r_question]:
            for first_children in r_object['children']:
                question_name = r_question+"/"+first_children['name']
                question_label = question_name
                
                if 'label' in first_children:
                    question_label = first_children['label']

                append_row(question_name, question_label, first_children['type'], r_answer)

    def parse_group( prev_groupname, g_object):
       
        g_question = prev_groupname+g_object['name']
        for first_children in g_object['children']:
            question_name = g_question+"/"+first_children['name']
            question_label = question_name

            if 'label' in first_children:
                question_label = first_children['label']
            
            append_row(question_name, question_label, first_children['type'], main_answer)
            
            # done at the end because wee want to print group name as well in report.
            if first_children['type'] == 'group':
                parse_group(g_question+"/",first_children)

    def parse_individual_questions():
       
        for first_children in main_question:
            if first_children['type'] == "repeat":
                parse_repeat(first_children)
            elif first_children['type'] == 'group':
                parse_group("", first_children)
            else:
                question_name = first_children['name']
                question_label = question_name

                if 'label' in first_children:
                    question_label = first_children['label']
                
                append_row(question_name, question_label, first_children['type'], main_answer)
    
    parse_individual_questions(question)

    return parsed_question, parsed_answer

class ExportOptions(ProjectRoleMixin, View):
    def get(self, request):
        return render(request, "fieldsight/fs_export/xls_export.html")

class ExportProjectSites(DonorRoleMixin, View):
    def get(self, *args, **kwargs):
        project=get_object_or_404(Project, pk=self.kwargs.get('pk'))
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="bulk_upload_sites.xls"'
        
        sites=project.sites.all().values('id')
        forms = FieldSightXF.objects.select_related('xf').filter(pk__in=fs_ids, is_survey=False, is_deleted=False).prefetch_related(Prefetch('site_form_instances', queryset=FInstance.objects.select_related('instance').filter(site_id__in=sites, date__range=[startdate, enddate]))).order_by('-is_staged', 'is_scheduled')
        
        for form in forms:

            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet(form.xf.title)
            # Sheet header, first row
            row_num = 1
            font_style = xlwt.XFStyle()
            head_columns = [{'question_name':'identifier','question_label':'identifier'}, {'question_name':'name','question_label':'name'}]
            
            questions = get_form_questions(form.xf.json)
            concat arrays

            for response in form.site_form_instances.all():
                questions, answers = parse_form_response(form.xf.json, response.instance.json)
                if len([{'question_name':'identifier','question_label':'identifier'}, {'question_name':'name','question_label':'name'}] + questions) > len(head_columns):
                    head_columns = [{'question_name':'identifier','question_label':'identifier'}, {'question_name':'name','question_label':'name'}] + questions  

                for col_num in range(len(head_columns)):
                    ws.write(row_num, col_num, answers[head_columns[col_num]['question_name']], font_style)
                row_num += 1

            font_style.font.bold = True
            for col_num in range(len(head_columns)):
                ws.write(row_num, col_num, head_columns[col_num]['question_label'], font_style)
        wb.save(response)
        return response

class ExportProjectSites(DonorRoleMixin, View):
    def get(self, *args, **kwargs):
        project=get_object_or_404(Project, pk=self.kwargs.get('pk'))
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="bulk_upload_sites.xls"'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Sites')
        # Sheet header, first row
        row_num = 0
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        columns = ['identifier', 'name', 'type', 'phone', 'address', 'public_desc', 'additional_desc', 'latitude',
                   'longitude', ]
        if project.cluster_sites:
            columns += ['region_id', ]
        meta_ques = project.site_meta_attributes
        for question in meta_ques:
            columns += [question['question_name']]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)
        row_num += 1

        font_style_unbold = xlwt.XFStyle()
        font_style_unbold.font.bold = False
        region_id = self.kwargs.get('region_id', None)
        sites = project.sites.all().order_by('identifier')

        if region_id:
            if region_id == "0":
                sites = project.sites.filter(region_id=None).order_by('identifier')
            else:
                sites = project.sites.filter(region_id=region_id).order_by('identifier')
        
        for site in sites:
            
            columns = [site.identifier, site.name, site.type.identifier if site.type else "", site.phone, site.address, site.public_desc, site.additional_desc, site.latitude,
                       site.longitude, ]
            
            if project.cluster_sites:
                if site.region:
                    columns += [site.region.identifier, ]
                else:
                    columns += ['', ]
            meta_ques = project.site_meta_attributes
            meta_ans = site.site_meta_attributes_ans
            for question in meta_ques:
                if question['question_name'] in meta_ans:
                    columns += [meta_ans[question['question_name']]]
                else:
                    columns += ['']
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style_unbold)
            row_num += 1
        wb.save(response)
        return response



class ExportProjectSitesWithRefs(DonorRoleMixin, View):
    def get(self, *args, **kwargs):
        project=get_object_or_404(Project, pk=self.kwargs.get('pk'))
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="bulk_upload_sites.xls"'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Sites')
        # Sheet header, first row
        
        header_columns = [{'id': 'identifier' ,'name':'identifier'},
                   {'id': 'name','name':'name'},
                   {'id': 'site_type_identifier','name':'type'}, 
                   {'id': 'phone','name':'phone'},
                   {'id': 'address','name':'address'},
                   {'id': 'public_desc','name':'public_desc'},
                   {'id': 'additional_desc','name':'additional_desc'},
                   {'id': 'latitude','name':'latitude'},
                   {'id': 'longitude','name':'longitude'}, ]
        if project.cluster_sites:
            header_columns += [{'id':'region_identifier', 'name':'region_id'}, ]
        meta_ques = project.site_meta_attributes
        for question in meta_ques:
            header_columns += [{'id': question['question_name'], 'name':question['question_name']}]
        
        
        region_id = self.kwargs.get('region_id', None)
        sites = project.sites.all().order_by('identifier')

        if region_id:
            if region_id == "0":
                sites = project.sites.filter(region_id=None).order_by('identifier')
            else:
                sites = project.sites.filter(region_id=region_id).order_by('identifier')
        site_list={}
        meta_ref_sites={}
        for site in sites:
            
            columns = {'identifier':site.identifier, 'name':site.name, 'site_type_identifier':site.type.identifier if site.type else "", 'phone':site.phone, 'address':site.address, 'public_desc':site.public_desc, 'additional_desc':site.additional_desc, 'latitude':site.latitude,
                       'longitude':site.longitude, }
            
            if project.cluster_sites:
                columns['region_identifier'] = site.region.identifier if site.region else ""
            
            meta_ques = project.site_meta_attributes
            meta_ans = site.site_meta_attributes_ans
            for question in meta_ques:
                if question['question_name'] in meta_ans:
                    columns[question['question_name']] = meta_ans[question['question_name']]

                    if question['question_type'] == "Link" and meta_ans[question['question_name']] != "":
                        if question.get('question_name') in meta_ref_sites:
                            meta_ref_sites[question.get('question_name')].append(meta_ans[question['question_name']])
                        else:
                            meta_ref_sites[question.get('question_name')] = [meta_ans[question['question_name']]]
                else:
                    columns[question['question_name']] = ''
            
            site_list[site.identifier] = columns
        

        def generate(project_id, site_map, meta, identifiers, selected_metas):
            project_id = str(project_id)
            sub_meta_ref_sites = {}
            sub_site_map = {}  
            sitenew = Site.objects.filter(identifier__in = identifiers, project_id = project_id)
            
            for site in sitenew:
                if project_id == str(project.id):
                    continue
            
                identifier = site_map.get(site.identifier)
                  
                if not site.site_meta_attributes_ans:
                    meta_ans = {}
                else:
                    meta_ans = site.site_meta_attributes_ans

                for meta in selected_metas.get(project_id, []):
                    
                    if meta.get('question_type') == "Link":
                        link_answer=str(meta_ans.get(meta.get('question_name'), ""))
                        if link_answer != "":    
                            if meta['question_name'] in sub_site_map:
                                if site.identifier in sub_site_map[meta['question_name']]:
                                    sub_site_map[meta['question_name']][link_answer].append(identifier)
                                else:
                                    sub_site_map[meta['question_name']][link_answer] = identifier
                            else:
                                sub_site_map[meta['question_name']] = {}
                                sub_site_map[meta['question_name']][link_answer] = identifier
                            
                            for idf in identifier:
                                if meta['question_name'] in sub_meta_ref_sites:
                                    sub_meta_ref_sites[meta['question_name']].append(meta_ans.get(meta['question_name']))
                                else:
                                    sub_meta_ref_sites[meta['question_name']] = [meta_ans.get(meta['question_name'])]

                    else:
                        for idf in identifier:
                            site_list[idf][project_id+"-"+meta.get('question_name')] = meta_ans.get(meta.get('question_name'), "")
                         
            for meta in selected_metas.get(project_id, []):
                head = header_columns
                head += [{'id':project_id+"-"+meta.get('question_name'), 'name':meta.get('question_text')}]
                if meta.get('question_type') == "Link":
                    generate(meta['project_id'], sub_site_map.get(meta['question_name'], []), meta, sub_meta_ref_sites.get(meta['question_name'], []), selected_metas)

        for meta in meta_ques:
            if meta['question_type'] == "Link":
                site_map = {}
                for key, value in site_list.items():
                    if value[meta['question_name']] != "":
                        identifier = str(value.get(meta['question_name']))
                        if identifier in site_map:
                            site_map[identifier].append(key)
                        else:
                            site_map[identifier] = [key]
                
                generate(meta['project_id'], site_map, meta, meta_ref_sites.get(meta['question_name'], []), meta.get('metas'))
        # import pdb; pdb.set_trace();
        row_num = 0
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        for col_num in range(len(header_columns)):
            ws.write(row_num, col_num, header_columns[col_num]['name'], font_style)
        row_num += 1

        font_style_unbold = xlwt.XFStyle()
        font_style_unbold.font.bold = False
        
        for key,site in site_list.iteritems():
            for col_num in range(len(header_columns)):
                ws.write(row_num, col_num, site.get(header_columns[col_num]['id'], ""), font_style_unbold)
            row_num += 1
        wb.save(response)
        return response


class CloneProjectSites(ProjectRoleMixin, View):
    def post(self, *args, **kwargs):
        try:
            f_project=get_object_or_404(Project, pk=self.kwargs.get('pk'))
            t_project=get_object_or_404(Project, pk=self.kwargs.get('t_pk'))
            body = json.loads(self.request.body)
            meta_attributes = body.get('meta_attributes', [])
            regions = body.get('regions', [])
            ignore_region = body.get('ignore_region', [])
            source_user = self.request.user            
            task_obj=CeleryTaskProgress.objects.create(user=source_user, task_type=4)
            if task_obj:
                task = importSites.delay(task_obj.pk, source_user, f_project, t_project, meta_attributes, regions, ignore_region)
                task_obj.task_id = task.id
                task_obj.save()
                result='Sites are being Imported. You will be notified in notifications list as well.'
            else:
                result = 'Sites cannot be imported a the moment.'
            return HttpResponse({result}, status=status.HTTP_200_OK)
        except Exception as e:
            return HttpResponse({'Site Import Failed, Contact Fieldsight Team'}, status=status.HTTP_200_OK)

# class CloneProjectSites(ProjectRoleMixin, View):
#     def post(self, *args, **kwargs):
#         f_project=get_object_or_404(Project, pk=self.kwargs.get('pk'))
#         t_project=get_object_or_404(Project, pk=self.kwargs.get('t_pk'))
#         body = json.loads(self.request.body)
        
#         meta_attributes = body.get('meta_attributes')
#         regions = body.get('regions')
#         ignore_region = body.get('ignore_region')
        
#         def filterbyquestion_name(seq, value):
#             for el in seq:
#                 if (not meta_attributes) or (meta_attributes and el.get('question_name') in meta_attributes):
#                     if el.get('question_name')==value:
#                         return True
#             return False
        
#         # migrate metas

#         if t_project.site_meta_attributes:
#             t_metas = t_project.site_meta_attributes
#             f_metas = f_project.site_meta_attributes
            
#             for f_meta in f_metas:
#                 # print t_metas
#                 # print ""
#                 check = filterbyquestion_name(t_metas, f_meta.get('question_name'))
#                 if not check:
#                     t_metas.append(f_meta)
#         region_map = {}      

#         t_project_sites = t_project.sites.all().values_list('identifier', flat=True)

#         # migrate regions
#         if f_project.cluster_sites and not ignore_region:
            
#             t_project_regions = t_project.project_region.all().values_list('identifier', flat=True)
#             t_project.cluster_sites=True
            
#             # To handle whole project or a single region migrate
#             region_objs = f_project.project_region.filter(id__in=regions)

#             for region in region_objs:
#                 f_region_id = region.id
#                 if region.identifier in t_project_regions:
#                     t_region_id = t_project.project_region.get(identifier=region.identifier).id
#                 else:
#                     region.id=None
#                     region.project_id=t_project.id
#                     region.save()
#                     t_region_id = region.id
#                 region_map[f_region_id]=t_region_id
        
#             t_project.save()

#             # getting Sites
        
#             sites = f_project.sites.filter(region_id__in=regions)
          
#             if 0 in regions:
#                 unassigned_sites = f_project.sites.filter(region_id=None)
#                 sites = sites | unassigned_sites

#         else:

#             sites = f_project.sites.all()

        
#         def get_t_region_id(f_region_id):
#             # To get new region id without a query
#             if f_region_id is not None and f_region_id in region_map:
#                 return region_map[f_region_id]
#             else:
#                 return None

#         # migrate sites
#         for site in sites:
#             site.id = None
#             site.project_id = t_project.id
            
#             if site.identifier in t_project_sites:
#                 site.identifier = str(site.identifier) + "IFP" + str(f_project.id)
        
#             if f_project.cluster_sites and not ignore_region:
#                 site.region_id = get_t_region_id(site.region_id)
#             else:
#                 site.region_id = None
            
#             site.save()
#         import pdb; pdb.set_trace();
#         return None
