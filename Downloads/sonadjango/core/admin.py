from django.contrib import admin 

from .models import  User, Employer, Candidate, Job, Application, ATSScore, EmailLog
admin.site.register(Employer)
admin.site.register(Candidate)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(ATSScore)
admin.site.register(EmailLog)
