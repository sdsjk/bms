/**
 * Created by dengel on 15/11/11.
 */
var jcsApp = angular.module('jcsApp',[]);
jcsApp.config(function($httpProvider) {

          // for xsrf token filter
          $httpProvider.defaults.xsrfCookieName = 'csrftoken';
          $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

          //for post data encoding
          $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
          $httpProvider.defaults.transformRequest = function(data){
                  if (data === undefined) {
                        return data;
                  }
                  return $.param(data);
          }
});
$(function(){
	/*
	 * Sidenav的Acitve状态判定.
	 */
	var nav_items = $("ul.nav.nav-pills>li");
	if(nav_items.size()>0){
		nav_items.each(function( index ) {
			if($(this).children("a").attr("href")==location.pathname){
				$(this).addClass("active");
				return false;
			}
		});

	}
});
